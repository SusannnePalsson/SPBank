
import os
import math
import pandas as pd
from datetime import datetime, date
from sqlalchemy import text, bindparam
from sqlalchemy.types import String, Date, Numeric
from db import engine

FLAGGED_CSV = "data/clean/flagged_transactions.csv"

def to_numeric_or_none(x):
    if x is None:
        return None
    s = str(x).strip()
    if s == "" or s.lower() in {"nan","none","null"}:
        return None
    try:
        v = float(s)
        return v if math.isfinite(v) else None
    except Exception:
        return None

def to_date_or_none(x):
    if not x:
        return None
    s = str(x).strip()
    if s == "" or s.lower() in {"nan","none","null"}:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s, fmt).date()
        except Exception:
            pass
    try:
        return pd.to_datetime(s).date()
    except Exception:
        return None

def main():
    if not os.path.exists(FLAGGED_CSV):
        print(f"[flagged] CSV saknas: {FLAGGED_CSV}")
        return

    df = pd.read_csv(FLAGGED_CSV, dtype=str, keep_default_na=False)
    print(f"[flagged] CSV-rader (exkl. header): {len(df)}")

    if "transaction_id" not in df.columns:
        if "id" in df.columns:
            df = df.rename(columns={"id": "transaction_id"})
        else:
            raise SystemExit("❌ flagged CSV saknar kolumnen 'transaction_id'.")

    inserted = skipped_existing = missing_tx = failed_rows = 0
    errors = []

    # NOTE: Justera CAST till TEXT om dina kolumner är TEXT i stället för VARCHAR.
    sql = text("""
        INSERT INTO bank.flagged_transactions (transaction_id, reason, flagged_date, amount)
        SELECT
            CAST(:tid AS VARCHAR),
            CAST(:reason AS TEXT),
            CAST(:date AS DATE),
            CAST(:amount AS NUMERIC)
        WHERE EXISTS (
            SELECT 1 FROM bank.transactions t
            WHERE t.id = CAST(:tid AS VARCHAR)
        )
        AND NOT EXISTS (
            SELECT 1
            FROM bank.flagged_transactions f
            WHERE f.transaction_id = CAST(:tid AS VARCHAR)
              AND f.reason = CAST(:reason AS TEXT)
              AND COALESCE(f.flagged_date::date, DATE '1970-01-01')
                  = COALESCE(CAST(:date AS DATE), DATE '1970-01-01')
        )
    """).bindparams(
        bindparam("tid", type_=String()),
        bindparam("reason", type_=String()),
        bindparam("date", type_=Date()),
        bindparam("amount", type_=Numeric())
    )

    with engine.begin() as conn:
        for i, r in df.iterrows():
            tid = str(r.get("transaction_id", "")).strip()
            reason = (str(r.get("reason", "")).strip() or "unspecified")[:500]
            date_val = to_date_or_none(r.get("flagged_date", ""))
            amount_val = to_numeric_or_none(r.get("amount", ""))

            params = {
                "tid": tid,
                "reason": reason,
                "date": None if date_val is None else date_val,
                "amount": None if amount_val is None else amount_val,
            }

            try:
                rc = conn.execute(sql, params).rowcount
                if rc:
                    inserted += 1
                else:
                    has_tx = conn.execute(
                        text("SELECT 1 FROM bank.transactions WHERE id = CAST(:tid AS VARCHAR)"),
                        {"tid": tid}
                    ).first()
                    if not has_tx:
                        print(f"❗ Hoppar över: Transaktion ID {tid} finns inte i databasen.")
                        missing_tx += 1
                    else:
                        skipped_existing += 1
            except Exception as e:
                failed_rows += 1
                errors.append(f"rad {i} (tid={tid}): {type(e).__name__}: {e}")

    print(f"[flagged] inserted={inserted}, skipped_existing={skipped_existing}, missing_tx={missing_tx}, failed_rows={failed_rows}")
    if errors:
        print("[flagged] exempel på fel (max 5):")
        for line in errors[:5]:
            print("   -", line)

if __name__ == "__main__":
    main()
