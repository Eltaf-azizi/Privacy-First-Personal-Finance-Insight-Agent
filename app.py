"""Streamlit multipage entry point."""
import streamlit as st

st.set_page_config(
    page_title="Privacy-First Finance Agent",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🔒 Privacy-First Personal Finance Agent")
st.caption("All processing is local. No data leaves this machine.")

st.markdown("""
### Welcome

Use the sidebar to navigate:

- **📊 Dashboard** — KPIs, category breakdown, trends, anomalies
- **💳 Transactions** — full table, filter, recategorise
- **🔮 Forecast** — predicted next-month spend + savings tracker
- **💬 Q&A** — ask questions about your data
- **⚙️ Settings** — upload a CSV, column mapping, LLM toggle
""")

from src.privacy import log_privacy_banner, audit
log_privacy_banner()
audit("APP_STARTUP", "Streamlit session started")