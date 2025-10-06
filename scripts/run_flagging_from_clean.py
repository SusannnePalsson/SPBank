# scripts/run_flagging_from_clean.py
import argparse
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd

from risk_rules import score_and_flag, RiskConfig

def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {
        "id": "transaction_id",
        "sender_acc": "from_account",
        "receiver_acc": "to_account",
        "from_acc": "from_account",
        "to_acc": "to_account",
    }
    cols = {c: rename_map.get(c, c) for c in df.columns}
    df = df.rename(columns=cols)
    return df

def main():
    ap = argparse.ArgumentParser(description="Kör flaggning direkt från redan städad CSV.")
    ap.add_argument("--in", dest="inp", default="data/clean/transactions_clean.csv", help="Infil (CSV)")
    ap.add_argument("--out", dest="out", default="data/clean/flagged_transactions.csv", help="Utfil (CSV)")
    ap.add_argument("--tz", dest="tz", default="Europe/Stockholm", help="Tidszon för flagged_date")
    args = ap.parse_args()

    in_path = Path(args.inp)
    out_path = Path(args.out)

    if not in_path.exists():
        raise SystemExit(f"Hittar inte {in_path}.")

    df = pd.read_csv(in_path, dtype=str, keep_default_na=False)
    if "amount" in df.columns:
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce")

    df = _normalize_columns(df)

    cfg = RiskConfig()
    flagged = score_and_flag(df, cfg)

    if "flagged_date" not in flagged.columns:
        flagged["flagged_date"] = datetime.now(ZoneInfo(args.tz)).date().isoformat()

    if "amount" not in flagged.columns and "transaction_id" in flagged.columns and "amount" in df.columns:
        flagged = flagged.merge(df[["transaction_id", "amount"]], on="transaction_id", how="left")

    cols = [c for c in ["transaction_id", "reason", "flagged_date", "amount"] if c in flagged.columns]
    flagged = flagged[cols].sort_values(["flagged_date", "amount"], ascending=[False, False])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    flagged.to_csv(out_path, index=False, encoding="utf-8")
    print(f"✅ Flaggade transaktioner sparade i {out_path} (antal={len(flagged)})")

if __name__ == "__main__":
    main()
