# scripts/run_flagging_from_db.py
import os
import argparse
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
from sqlalchemy import create_engine, text

from risk_rules import score_and_flag, RiskConfig

DEFAULT_DB = "postgresql+psycopg://postgres:postgres@localhost:5432/bank"

SQL = """select
  id as transaction_id,
  timestamp,
  amount,
  currency,
  sender_acc as from_account,
  receiver_acc as to_account,
  sender_country,
  receiver_country,
  notes
from bank.transactions
"""

def main():
    ap = argparse.ArgumentParser(description="Kör flaggning direkt från DB (bank.transactions).")
    ap.add_argument("--db", dest="db", default=os.getenv("DATABASE_URL", DEFAULT_DB), help="DATABASE_URL")
    ap.add_argument("--out", dest="out", default="data/clean/flagged_transactions.csv", help="Utfil (CSV)")
    ap.add_argument("--tz", dest="tz", default="Europe/Stockholm", help="Tidszon för flagged_date")
    args = ap.parse_args()

    db_url = args.db
    if "options=" not in db_url:
        sep = "&" if "?" in db_url else "?"
        db_url = f"{db_url}{sep}options=-csearch_path%3Dbank%2Cpublic"

    engine = create_engine(db_url, future=True)
    with engine.begin() as conn:
        df = pd.read_sql(text(SQL), conn)

    if "amount" in df.columns:
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce")

    cfg = RiskConfig()
    flagged = score_and_flag(df, cfg)

    if "flagged_date" not in flagged.columns:
        flagged["flagged_date"] = datetime.now(ZoneInfo(args.tz)).date().isoformat()

    if "amount" not in flagged.columns and "amount" in df.columns:
        flagged = flagged.merge(df[["transaction_id","amount"]], on="transaction_id", how="left")

    cols = [c for c in ["transaction_id", "reason", "flagged_date", "amount"] if c in flagged.columns]
    flagged = flagged[cols].sort_values(["flagged_date", "amount"], ascending=[False, False])
    out_path = os.fspath(os.path.normpath(args.out))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    flagged.to_csv(out_path, index=False, encoding="utf-8")
    print(f"✅ Sparade {out_path} (antal={len(flagged)})")

if __name__ == "__main__":
    main()
