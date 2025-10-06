
from prefect import flow, task
import subprocess
import sys
import re
from sqlalchemy import text
from db import engine
from init_schema import ensure_schema

SUMMARY_PATTERNS = {
    "customers": re.compile(r"\[customers\]\s+inserted=(\d+),\s+skipped_existing=(\d+)", re.I),
    "accounts":  re.compile(r"\[accounts\s*\]\s+inserted=(\d+),\s+skipped_existing=(\d+),\s+missing_owner=(\d+)", re.I),
    "transactions": re.compile(r"\[transactions\]\s+inserted=(\d+),\s+skipped_existing=(\d+),\s+missing_accounts=(\d+)", re.I),
    "flagged": re.compile(r"\[flagged\]\s+inserted=(\d+),\s+skipped_existing=(\d+),\s+missing_tx=(\d+)", re.I),
}

def run_and_capture(cmd: list[str], title: str):
    print(f"▶ {title}: {' '.join(cmd)}")
    proc = subprocess.run(cmd, text=True, capture_output=True, check=True)
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, end="")
    return proc.stdout + "\n" + proc.stderr

def extract_summary(whole_output: str):
    summary = {}
    for key, pat in SUMMARY_PATTERNS.items():
        m = pat.search(whole_output)
        if m:
            summary[key] = tuple(int(x) for x in m.groups())
    return summary

def db_counts():
    q = """
    SELECT 'customers' AS t, COUNT(*) FROM bank.customers
    UNION ALL
    SELECT 'accounts', COUNT(*) FROM bank.accounts
    UNION ALL
    SELECT 'transactions', COUNT(*) FROM bank.transactions
    UNION ALL
    SELECT 'flagged', COUNT(*) FROM bank.flagged_transactions
    """
    res = {}
    with engine.connect() as c:
        for name, cnt in c.execute(text(q)):
            res[name] = int(cnt)
    return res

def flagged_reason_stats(limit_examples:int=10):
    """Returnerar (lista med (reason, n)) och exempelrader med kontext."""
    top_q = text("""
        SELECT reason, COUNT(*) AS n
        FROM bank.flagged_transactions
        GROUP BY reason
        ORDER BY n DESC, reason ASC
    """)
    examples_q = text("""
        SELECT f.flagged_date, f.amount, f.reason,
               t.id, t.timestamp, t.currency,
               sa.account_number AS sender_acc, ra.account_number AS receiver_acc,
               t.sender_country, t.receiver_country
        FROM bank.flagged_transactions f
        JOIN bank.transactions t ON t.id = f.transaction_id
        LEFT JOIN bank.accounts sa ON sa.id = t.sender_account_id
        LEFT JOIN bank.accounts ra ON ra.id = t.receiver_account_id
        ORDER BY f.flagged_date DESC, f.amount DESC
        LIMIT :lim
    """)
    with engine.connect() as c:
        top = list(c.execute(top_q))
        ex = list(c.execute(examples_q, {"lim": limit_examples}))
    return top, ex

@task
def init_schema_task():
    print("▶ Säkerställer att schema/tabeller finns...")
    ensure_schema()
    print("✅ Schema/tabeller OK.")

@task
def run_validation_task():
    return run_and_capture([sys.executable, "validation.py"], "Kör validering")

@task
def import_customers_task():
    out = run_and_capture([sys.executable, "import_customers.py"], "Import customers")
    counts = db_counts()
    print(f"🔎 DB efter customers/accounts → customers={counts.get('customers',0)}, accounts={counts.get('accounts',0)}")
    if counts.get('customers',0) == 0 or counts.get('accounts',0) == 0:
        print("⚠️ VARNING: Inga kunder eller konton insatta.")
    return out

@task
def import_transactions_task():
    out = run_and_capture([sys.executable, "import_transactions.py"], "Import transactions")
    counts = db_counts()
    print(f"🔎 DB efter transactions → transactions={counts.get('transactions',0)}")
    if counts.get('transactions',0) == 0:
        print("⚠️ VARNING: Inga transaktioner insatta.")
    return out

@task
def import_flagged_task():
    out = run_and_capture([sys.executable, "import_flagged_transactions.py"], "Import flagged transactions")
    counts = db_counts()
    print(f"🔎 DB efter flagged → flagged={counts.get('flagged',0)}")
    if counts.get('flagged',0) == 0:
        print("ℹ️ Info: flagged_transactions är tomt. Justera regler/trösklar och kör om validation.")
    return out

@task
def reporting_task():
    print("\n🧾 Rapport: Flagged-transaktioner (översikt)\n" + "-"*60)
    counts = db_counts()
    print(f"Antal rader i flagged_transactions: {counts.get('flagged',0)}\n")
    if counts.get('flagged',0) == 0:
        print("(Inget att visa ännu.)")
        return
    top, ex = flagged_reason_stats(limit_examples=10)
    if top:
        print("Toppreasons (antal):")
        for reason, n in top[:10]:
            print(f" - {n:>6} ×  {reason}")
    else:
        print("(Inga reason-grupper hittades.)")
    if ex:
        print("\nExempel (10 senaste/största):")
        header = ("flagged_date","amount","reason","id","timestamp","currency","sender_acc","receiver_acc","sender_country","receiver_country")
        print(" | ".join(header))
        for row in ex:
            values = [str(row._mapping[k]) if k in row._mapping else str(row[i]) for i, k in enumerate(header)]
            print(" | ".join(values))
    print("-"*60 + "\n")


@flow(name="ETL-bank-flow")
def full_pipeline():
    init_schema_task()
    out1 = run_validation_task()
    out2 = import_customers_task()
    out3 = import_transactions_task()
    out4 = import_flagged_task()

    # Summering
    all_out = "\n".join([out1, out2, out3, out4])
    s = extract_summary(all_out)
    counts = db_counts()

    print("\n" + "="*72)
    print("ETL-sammanfattning • Summeringar + DB-kontroller")
    print("="*72)
    if "customers" in s:
        ins, skip = s["customers"]
        print(f"Customers      → inserted={ins}, skipped_existing={skip}  | DB: {counts.get('customers',0)}")
    if "accounts" in s:
        ins, skip, miss = s["accounts"]
        print(f"Accounts       → inserted={ins}, skipped_existing={skip}, missing_owner={miss}  | DB: {counts.get('accounts',0)}")
    if "transactions" in s:
        ins, skip, miss = s["transactions"]
        print(f"Transactions   → inserted={ins}, skipped_existing={skip}, missing_accounts={miss}  | DB: {counts.get('transactions',0)}")
    if "flagged" in s:
        ins, skip, miss = s["flagged"]
        print(f"Flagged tx     → inserted={ins}, skipped_existing={skip}, missing_tx={miss}  | DB: {counts.get('flagged',0)}")
    print("-"*72)
    ok = True
    if counts.get('customers',0) == 0 or counts.get('accounts',0) == 0:
        ok = False
    if counts.get('transactions',0) == 0:
        ok = False
    print("STATUS:", "OK ✅" if ok else "KONTROLLERA ⚠️")
    print("="*72)

    # Extra: svensk rapport för flagged
    reporting_task()

if __name__ == "__main__":
    full_pipeline()
