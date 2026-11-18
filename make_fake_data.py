"""Synthetic data generator (includes hidden ground-truth labels)."""
import random
import pandas as pd
from datetime import date, timedelta

random.seed(42)

MERCHANTS = {
    "Groceries": [("WALMART", 15, 80), ("TESCO", 10, 60), ("ALDI", 8, 50),
                  ("LIDL", 8, 45), ("SAINSBURY", 12, 65)],
    "Transport": [("UBER", 5, 25), ("SHELL", 30, 70), ("TFL", 3, 10),
                  ("BP", 30, 70)],
    "Dining":    [("STARBUCKS", 3, 9), ("MCDONALD'S", 4, 12),
                  ("PRET", 5, 14), ("DELIVEROO", 15, 40)],
    "Utilities": [("BRITISH GAS", 40, 90), ("THAMES WATER", 25, 45),
                  ("OCTOPUS ENERGY", 30, 80)],
    "Shopping":  [("AMAZON", 10, 120), ("ARGOS", 20, 150), ("ASOS", 20, 80)],
    "Health":    [("BOOTS", 5, 30), ("PUREGYM", 20, 30)],
    "Entertainment": [("NETFLIX", 8, 15), ("SPOTIFY", 8, 12)],
}

rows = []
start = date(2026, 1, 1)


# 400 normal transactions over Jan–Jun 2026 (6 months for forecast)
for _ in range(400):
    cat = random.choice(list(MERCHANTS))
    name, lo, hi = random.choice(MERCHANTS[cat])
    d = start + timedelta(days=random.randint(0, 180))
    rows.append([d, name, -round(random.uniform(lo, hi), 2), cat])

# Monthly income
for month in range(6):
    d = date(2026, month + 1, 28)
    rows.append([d, "SALARY ACME LTD", 2500.00, "Income"])

# 8 planted anomalies
for _ in range(8):
    d = start + timedelta(days=random.randint(0, 180))
    rows.append([d, "AMAZON", -round(random.uniform(400, 900), 2), "Shopping"])

# 10 unclear merchants → Other
for merchant in ["CORNER SHOP 4521", "MR K SMITH", "PAYPAL TRANSFER"]:
    for _ in range(3):
        d = start + timedelta(days=random.randint(0, 180))
        rows.append([d, merchant, -round(random.uniform(5, 40), 2), "Other"])

# 12 café rows → Dining (caught by CAFE keyword)
for _ in range(12):
    d = start + timedelta(days=random.randint(0, 180))
    rows.append([d, "SQ *CAFE 88", -round(random.uniform(4, 12), 2), "Dining"])

df = pd.DataFrame(rows, columns=["Date", "Description", "Amount", "true_category"])
df = df.sort_values("Date").reset_index(drop=True)
df.to_csv("data/fake_transactions.csv", index=False)
print(f"Wrote {len(df)} transactions")
print(df["true_category"].value_counts().to_string())