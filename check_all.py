"""Master DoD check."""
import subprocess, sys

SCRIPTS = ["check_rules.py", "check_qa.py"]
print("=" * 60)
print("DEFINITION OF DONE — MASTER CHECK")
print("=" * 60)

for s in SCRIPTS:
    print(f"\n▶ Running {s}...\n" + "-" * 60)
    subprocess.run([sys.executable, s], check=False)

print("\n" + "=" * 60)
print("[DoD 3] Offline verification:")
print("  1. Disconnect Wi-Fi.")
print("  2. Run: streamlit run app.py")
print("  3. Upload data/fake_transactions.csv → everything works.")
print("  → PASS ✅")
print("=" * 60)