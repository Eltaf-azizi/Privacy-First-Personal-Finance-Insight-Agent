"""Merchant-name normalisation — strips noise so rules match more rows."""
from __future__ import annotations

import re

NOISE = [
    r"\b\d{4,}\b",                     # long card / reference numbers
    r"\b(pos|card|txn|ref|trx)\b",
    r"\b\d{2}/\d{2}(/\d{2,4})?\b",      # embedded dates
    r"[*#]",                            # often prefixes Square/PayPal
    r"\s{2,}",
]

_PATTERNS = [re.compile(p, re.IGNORECASE) for p in NOISE]


def normalise(desc: str) -> str:
    """Return an upper-cased, noise-stripped merchant name."""
    if not isinstance(desc, str):
        return ""
    s = desc.upper()
    for pat in _PATTERNS:
        s = pat.sub(" ", s)
    return " ".join(s.split())