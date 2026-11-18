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
