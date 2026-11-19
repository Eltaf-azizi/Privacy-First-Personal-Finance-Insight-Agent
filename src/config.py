"""Central configuration loader."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import yaml


CONFIG_PATH = Path(__file__).parent.parent / "config" / "config.yaml"


@lru_cache(maxsize=1)
def load_config() -> dict:
    """Load and cache the YAML configuration."""
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Config not found: {CONFIG_PATH}")
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get(section: str, key: str, default=None):
    """Dot-access helper: config.get('anomaly', 'z_threshold', 2.5)."""
    return load_config().get(section, {}).get(key, default)


def ensure_dirs() -> None:
    """Create runtime directories if missing."""
    base = Path(__file__).parent.parent
    for sub in ["data", "data/logs"]:
        (base / sub).mkdir(parents=True, exist_ok=True)