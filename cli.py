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


def cmd_ask(args):
    df = load_from_db()
    if df.empty:
        sys.exit("No data — run `python cli.py ingest <path>` first.")
    print(answer_question(args.question, df))


def cmd_report(args):
    df = load_from_db()
    if df.empty:
        sys.exit("No data.")
    print("=== Monthly summary ===")
    print(monthly_summary(df).to_string(index=False))
    print("\n=== Spend by category ===")
    print(spend_by_category(df).to_string(index=False))


def cmd_check(args):
    """Run the check_* scripts for DoD verification."""
    import subprocess
    for script in ["check_rules.py", "check_qa.py"]:
        print(f"\n━━━ {script} ━━━")
        subprocess.run([sys.executable, script], check=False)


def cmd_export(args):
    df = load_from_db()
    if df.empty:
        sys.exit("No data.")
    df.to_csv(args.out, index=False)
    print(f"✅ Exported {len(df)} rows → {args.out}")


def main():
    p = argparse.ArgumentParser(description="Privacy-First Finance Agent CLI")
    sub = p.add_subparsers(dest="command", required=True)

    pi = sub.add_parser("ingest", help="Load, categorise, save a CSV")
    pi.add_argument("path")
    pi.add_argument("--llm", action="store_true", help="Use LLM fallback")
    pi.set_defaults(func=cmd_ingest)

    pa = sub.add_parser("ask", help="Ask a natural-language question")
    pa.add_argument("question")
    pa.set_defaults(func=cmd_ask)

    pr = sub.add_parser("report", help="Print summaries")
    pr.set_defaults(func=cmd_report)

    pc = sub.add_parser("check", help="Run DoD checks")
    pc.set_defaults(func=cmd_check)

    pe = sub.add_parser("export", help="Export transactions to CSV")
    pe.add_argument("out")
    pe.set_defaults(func=cmd_export)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()