"""Categorisation accuracy check — DoD 1."""
import pandas as pd
from src.ingest import load_transactions
from src.categorise import categorise

raw = pd.read_csv("data/fake_transactions.csv")
df = categorise(load_transactions("data/fake_transactions.csv"), use_llm=False)
df["true_category"] = raw["true_category"].values

correct = (df["category"] == df["true_category"]).sum()
total = len(df)
pct = correct / total * 100

print(f"Total rows:            {total}")
print(f"Correct:               {correct}/{total} = {pct:.1f}%")
print(f"Status:                {'PASS ✅' if pct >= 90 else 'FAIL ❌'}")
print("\nPer-category accuracy:")
for cat in df["true_category"].unique():
    s = df[df["true_category"] == cat]
    acc = (s["category"] == cat).mean() * 100
    print(f"  {cat:15s} {acc:5.1f}%  ({len(s)} rows)")
print("\nConfidence distribution:")
print(df["confidence"].describe().round(2).to_string())