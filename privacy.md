# Privacy Guarantee

**No financial data leaves this machine.**

## What runs locally

| Component | Location |
|---|---|
| CSV parsing, pandas, analytics | `src/*.py` |
| Categorisation (rules + ML) | `src/categorise.py` |
| SQLite storage | `data/transactions.db`, `data/corrections.db` |
| LLM inference (optional) | Ollama on `http://localhost:11434` |
| Streamlit dashboard | `http://localhost:8501` |
| Audit logs | `data/privacy_audit.log`, `data/app.log` |

## What the LLM receives

Only merchant **descriptions** for rows the rules engine cannot classify,
or **aggregated** category totals for Q&A fallback. Never:
- Account numbers
- Balances
- Full raw row sets
- Any personal identifier

## Enforcement

`src/privacy.py` exposes `assert_local(url)`, which **raises** if any URL
does not resolve to loopback. It is called before every outbound HTTP
request in `src/categorise.py` and `src/qa.py`. All blocked attempts are
audited to `data/privacy_audit.log`.

## Verification

1. Disconnect Wi-Fi.
2. `streamlit run app.py` → dashboard works.
3. `python cli.py ask "how much on dining in march?"` → answer returned.
4. Inspect `data/privacy_audit.log` — every entry is either `STARTUP`,
   `QA_QUERY`, or `ALLOWED_LOCAL_CALL`.