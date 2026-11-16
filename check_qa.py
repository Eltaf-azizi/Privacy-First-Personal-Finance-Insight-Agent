"""Q&A accuracy check — DoD 2."""
import pandas as pd
from src.ingest import load_transactions
from src.categorise import categorise
from src.anomaly import flag_anomalies
from src.qa import answer_question

df = flag_anomalies(categorise(load_transactions("data/fake_transactions.csv"), use_llm=False))

dining_march = df[(df.category=="Dining") & (df.date.dt.month==3)]["amount"].sum()
biggest = df.groupby("category")["amount"].sum().abs().idxmax()
total = df[df.amount<0]["amount"].sum()
transport_jan = df[(df.category=="Transport") & (df.date.dt.month==1)]["amount"].sum()
anomalies = int(df["is_anomaly"].sum())

tests = [
    ("how much on dining in march?", f"£{abs(dining_march):,.2f}"),
    ("what is my biggest category?", biggest),
    ("what is my total spend?", f"£{abs(total):,.2f}"),
    ("how much on transport in january?", f"£{abs(transport_jan):,.2f}"),
    ("are there any unusual transactions?", str(anomalies)),
]

print("=" * 60)
print("Q&A ACCURACY — DoD 2")
print("=" * 60)
passed = 0
for q, expected in tests:
    a = answer_question(q, df)
    ok = expected in a
    passed += ok
    print(f"{'PASS ✅' if ok else 'FAIL ❌'} | {q}")
    print(f"        → {a}")
    print(f"        (expected fragment: {expected})\n")

print(f"Result: {passed}/{len(tests)} correct")
print("Status: " + ("PASS ✅" if passed == len(tests) else "FAIL ❌"))