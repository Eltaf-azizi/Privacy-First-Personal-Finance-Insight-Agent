"""
Command-line interface — run the whole pipeline without the UI.

Usage:
    python cli.py ingest data/fake_transactions.csv
    python cli.py ask "how much on dining in march?"
    python cli.py report
    python cli.py check
    python cli.py export report.csv
"""
from __future__ import annotations

import argparse
import sys

from src.ingest import load_transactions
from src.categorise import categorise
from src.anomaly import flag_anomalies
from src.analytics import monthly_summary, spend_by_category
from src.qa import answer_question
from src.storage import save_transactions, load_transactions as load_from_db


def cmd_ingest(args):
    df = load_transactions(args.path)
    df = categorise(df, use_llm=args.llm)
    df = flag_anomalies(df)
    save_transactions(df)
    print(f"✅ Ingested {len(df)} transactions")
    print(df.head())
