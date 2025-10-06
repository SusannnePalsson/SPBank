
import pandas as pd
from sqlalchemy import text
from db import engine

TX_CSV = "data/clean/transactions_clean.csv"

def to_dt(x):
    if pd.isna(x) or x == "":
        return None
    try:
        return pd.to_datetime(x).to_pydatetime()
    except Exception:
        return None

def main():
    df = pd.read_csv(TX_CSV, dtype=str, keep_default_na=False)

    # Stöd både 'id' och 'transaction_id'
    if "id" not in df.columns and "transaction_id" in df.columns:
        df = df.rename(columns={"transaction_id":"id"})
    # Timestamp -> datetime
    if "timestamp" in df.columns:
        df["timestamp"] = df["timestamp"].apply(to_dt)

    inserted = skipped_existing = missing_accounts = 0

    sql = text("""
        INSERT INTO bank.transactions (
            id, timestamp, amount, currency, notes,
            sender_account_id, receiver_account_id,
            sender_country, sender_municipality, receiver_country, receiver_municipality,
            transaction_type
        )
        SELECT
            :id, :timestamp, :amount, :currency, NULLIF(:notes,''),
            (SELECT id FROM bank.accounts WHERE account_number=:sender_acc),
            (SELECT id FROM bank.accounts WHERE account_number=:receiver_acc),
            NULLIF(:sc,''), NULLIF(:sm,''), NULLIF(:rc,''), NULLIF(:rm,''),
            NULLIF(:tt,'')
        ON CONFLICT (id) DO NOTHING
    """)

    with engine.begin() as conn:
        for _, r in df.iterrows():
            params = dict(
                id=str(r.get("id","")).strip(),
                timestamp=r.get("timestamp", None),
                amount=float(r.get("amount", 0) or 0),
                currency=str(r.get("currency","")).strip() or None,
                notes=str(r.get("notes","")).strip(),
                sender_acc=str(r.get("sender_account","") or r.get("sender_account_number","")).strip(),
                receiver_acc=str(r.get("receiver_account","") or r.get("receiver_account_number","")).strip(),
                sc=str(r.get("sender_country","")).strip(),
                sm=str(r.get("sender_municipality","")).strip(),
                rc=str(r.get("receiver_country","")).strip(),
                rm=str(r.get("receiver_municipality","")).strip(),
                tt=str(r.get("transaction_type","")).strip(),
            )
            rc = conn.execute(sql, params).rowcount
            if rc:
                inserted += 1
            else:
                s_ok = conn.execute(text("SELECT 1 FROM bank.accounts WHERE account_number=:a"), {"a": params["sender_acc"]}).first()
                r_ok = conn.execute(text("SELECT 1 FROM bank.accounts WHERE account_number=:a"), {"a": params["receiver_acc"]}).first()
                if not s_ok or not r_ok:
                    missing_accounts += 1
                else:
                    skipped_existing += 1

    print(f"[transactions] inserted={inserted}, skipped_existing={skipped_existing}, missing_accounts={missing_accounts}")

if __name__ == "__main__":
    main()
