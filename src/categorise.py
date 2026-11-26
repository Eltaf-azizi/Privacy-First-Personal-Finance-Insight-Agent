"""
Multi-tier categorisation:
  Tier 1 — deterministic keyword rules (highest confidence)
  Tier 2 — previously-learned corrections (from user feedback)
  Tier 3 — local LLM (Ollama, only for unmatched)
  Tier 4 — ML classifier (Naive Bayes trained on labelled sample)
  Fallback — "Other"

No data leaves the machine. Only Tier 3 makes any network call, and it
is hard-restricted to localhost via src.privacy.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import pandas as pd

from .config import get
from .logger import get_logger
from .privacy import assert_local, audit

_log = get_logger(__name__)

RULES: dict[str, list[str]] = {
    "Groceries": ["WALMART", "TESCO", "ALDI", "LIDL", "SAINSBURY", "MORRISONS", "COSTCO", "WHOLE FOODS"],
    "Transport": ["UBER", "LYFT", "SHELL", "BP", "TFL", "OYSTER", "TRAINLINE", "NATIONAL RAIL", "EXXON"],
    "Dining":    ["STARBUCKS", "MCDONALD", "PRET", "DELIVEROO", "JUST EAT", "CAFE", "RESTAURANT", "NANDO"],
    "Utilities": ["BRITISH GAS", "THAMES WATER", "OCTOPUS", "EDF", "E.ON", "SCOTTISH POWER", "TV LICENCE"],
    "Shopping":  ["AMAZON", "ARGOS", "EBAY", "ASOS", "ZARA", "H&M", "IKEA"],
    "Health":    ["BOOTS", "PHARMACY", "NHS", "DENTAL", "GYM", "PUREGYM"],
    "Entertainment": ["NETFLIX", "SPOTIFY", "DISNEY", "STEAM", "PLAYSTATION", "CINEMA", "VUE"],
}

CATEGORIES = sorted(list(RULES.keys()) + ["Income", "Other"])



# ---- Tier 1: rules ---------------------------------------------------------

def apply_rules(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["category"] = pd.NA
    df["confidence"] = 0.0
    text = df["merchant"].fillna("").astype(str)
    for cat, keywords in RULES.items():
        for kw in keywords:
            mask = text.str.contains(kw, na=False) & df["category"].isna()
            df.loc[mask, "category"] = cat
            df.loc[mask, "confidence"] = 1.0
    return df



# ---- Tier 2: learned corrections ------------------------------------------

CORRECTIONS_DB = Path("data/corrections.db")


def load_corrections() -> dict[str, str]:
    if not CORRECTIONS_DB.exists():
        return {}
    import sqlite3
    conn = sqlite3.connect(CORRECTIONS_DB)
    try:
        rows = conn.execute("SELECT merchant, category FROM corrections").fetchall()
    except sqlite3.OperationalError:
        rows = []
    conn.close()
    return {m: c for m, c in rows}


def save_correction(merchant: str, category: str) -> None:
    import sqlite3
    CORRECTIONS_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(CORRECTIONS_DB)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS corrections (merchant TEXT PRIMARY KEY, category TEXT)"
    )
    conn.execute(
        "INSERT OR REPLACE INTO corrections (merchant, category) VALUES (?, ?)",
        (merchant, category),
    )
    conn.commit()
    conn.close()
    _log.info("Saved correction: %s → %s", merchant, category)


def apply_corrections(df: pd.DataFrame) -> pd.DataFrame:
    corrections = load_corrections()
    if not corrections:
        return df
    mask = df["category"].isna() & df["merchant"].isin(corrections)
    df.loc[mask, "category"] = df.loc[mask, "merchant"].map(corrections)
    df.loc[mask, "confidence"] = 0.95
    return df



# ---- Tier 3: local LLM -----------------------------------------------------

def _ask_ollama(description: str) -> tuple[str, float]:
    import requests
    url = get("categorise", "llm_endpoint", "http://localhost:11434/api/generate")
    assert_local(url)  # raises if non-local
    model = get("categorise", "llm_model", "llama3.2")
    prompt = (
        f"Categorise into one of: {', '.join(CATEGORIES)}.\n"
        f"Transaction: '{description}'\nReply with category only."
    )
    try:
        r = requests.post(
            url,
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=30,
        )
        out = r.json().get("response", "").strip().split()[0].strip(".,'\"")
        if out in CATEGORIES:
            audit("LLM_CATEGORISE", f"{description[:40]} -> {out}")
            return out, 0.75
    except Exception as e:
        _log.warning("LLM call failed: %s", e)
    return "Other", 0.1



# ---- Tier 4: ML fallback ---------------------------------------------------

_ML_MODEL = None


def _train_ml(df: pd.DataFrame) -> None:
    """Train a tiny Naive Bayes on rows already labelled by rules."""
    global _ML_MODEL
    try:
        from sklearn.feature_extraction.text import CountVectorizer
        from sklearn.naive_bayes import MultinomialNB
        from sklearn.pipeline import Pipeline
    except ImportError:
        _log.info("scikit-learn not installed — ML fallback disabled")
        _ML_MODEL = None
        return

    labelled = df[df["category"].notna() & (df["confidence"] >= 0.9)]
    if len(labelled) < 30 or labelled["category"].nunique() < 2:
        _ML_MODEL = None
        return

    model = Pipeline([
        ("vec", CountVectorizer(ngram_range=(1, 2))),
        ("nb", MultinomialNB()),
    ])
    model.fit(labelled["merchant"], labelled["category"])
    _ML_MODEL = model
    _log.info("ML fallback trained on %d labelled rows", len(labelled))


def _apply_ml(df: pd.DataFrame) -> pd.DataFrame:
    if _ML_MODEL is None:
        return df
    mask = df["category"].isna()
    if not mask.any():
        return df
    try:
        preds = _ML_MODEL.predict(df.loc[mask, "merchant"])
        proba = _ML_MODEL.predict_proba(df.loc[mask, "merchant"]).max(axis=1)
        # Only trust high-confidence predictions
        confident = proba >= 0.5
        idx = df.loc[mask].index
        df.loc[idx[confident], "category"] = preds[confident]
        df.loc[idx[confident], "confidence"] = proba[confident] * 0.6
    except Exception as e:
        _log.warning("ML fallback error: %s", e)
    return df



# ---- Orchestrator ----------------------------------------------------------

def categorise(
    df: pd.DataFrame,
    use_llm: bool = None,
    use_ml: bool = None,
) -> pd.DataFrame:
    if use_llm is None:
        use_llm = get("categorise", "use_llm", False)
    if use_ml is None:
        use_ml = get("categorise", "use_ml_fallback", True)

    df = apply_rules(df)
    df = apply_corrections(df)

    unclear = df["category"].isna()
    if unclear.any() and use_llm:
        results = df.loc[unclear, "merchant"].apply(_ask_ollama)
        df.loc[unclear, "category"] = [c for c, _ in results]
        df.loc[unclear, "confidence"] = [p for _, p in results]

    if use_ml:
        _train_ml(df)          # train on rule-labelled portion
        df = _apply_ml(df)

    df["category"] = df["category"].fillna("Other")
    df["confidence"] = df["confidence"].fillna(0.0).clip(0, 1).round(2)

    _log.info("Categorised %d rows (confidence mean %.2f)",
              len(df), df["confidence"].mean())
    return df
    