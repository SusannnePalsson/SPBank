# validation.py
import pandas as pd
from pathlib import Path
from risk_rules import score_and_flag, RiskConfig

# Infilernas faktiska namn i ditt projekt
CUSTOMERS_IN = Path("data/sebank_customers_with_accounts.csv")
# CUSTOMERS_IN = Path("data/sebank_customers_with_accounts-5000-10000.csv")
TX_IN = Path("data/transactions.csv")
# TX_IN = Path("data/transactions-500000.csv")

# Output-mapp
OUT_DIR = Path("data/clean")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def clean_customers():
    if not CUSTOMERS_IN.exists():
        raise FileNotFoundError(f"Hittar inte kundfilen: {CUSTOMERS_IN}")

    df = pd.read_csv(CUSTOMERS_IN, dtype=str, keep_default_na=False)
    print(f"Totalt kunder innan validering: {len(df)}")

    # Säkerställ kolumnnamn (de finns redan så detta är mest explicit)
    df = df.rename(columns={
        "Customer": "Customer",
        "Personnummer": "Personnummer",
        "BankAccount": "BankAccount",
        "Address": "Address",
        "Phone": "Phone",
    })

    # Grundkrav
    df = df[(df["Customer"].str.strip() != "") & (df["BankAccount"].str.strip() != "")]
    print(f"Efter dropna på Customer och BankAccount: {len(df)}")

    # Telefon — tillåt tomt, annars minst 7 tecken (enkelt krav)
    def valid_phone(x: str) -> bool:
        x = str(x).strip()
        return (x == "") or (len(x) >= 7)

    df = df[df["Phone"].apply(valid_phone)]
    print(f"Efter telefonfilter: {len(df)}")

    # Personnummer: enkelt format XXXXXX-XXXX
    def valid_pnr(x: str) -> bool:
        x = str(x).strip()
        return len(x) == 11 and x[6] == "-"

    df = df[df["Personnummer"].apply(valid_pnr)]
    print(f"Efter personnummerfilter: {len(df)}")

    # En kund per konto
    df = df.drop_duplicates(subset=["BankAccount"], keep="first")
    print(f"Efter drop_duplicates på BankAccount: {len(df)}")

    out = OUT_DIR / "customers_clean.csv"
    df.to_csv(out, index=False)
    print(f"\nKunddata sparad i {out}\n")


def clean_transactions():
    if not TX_IN.exists():
        raise FileNotFoundError(f"Hittar inte transaktionsfilen: {TX_IN}")

    df = pd.read_csv(TX_IN, dtype=str, keep_default_na=False)
    print(f"Totalt transaktioner innan validering: {len(df)}")

    # amount -> float och >= 0.01
    def to_float_ok(x):
        try:
            return float(x)
        except Exception:
            return None

    df["amount"] = df["amount"].apply(to_float_ok)
    df = df[df["amount"].apply(lambda v: isinstance(v, float) and v >= 0.01)]
    print(f"Efter filter på amount >= 0.01: {len(df)}")

    # Begränsa valutor (justera vid behov)
    allowed = {"SEK", "USD", "EUR", "GBP", "NOK", "DKK"}
    if "currency" in df.columns:
        df = df[df["currency"].isin(allowed)]
    print(f"Efter valutafilter: {len(df)}")

    # notes aldrig NaN
    if "notes" in df.columns:
        df["notes"] = df["notes"].fillna("")
    print(f"Efter dropna på notes: {len(df)}")

    # unika transaktioner
    key = "transaction_id" if "transaction_id" in df.columns else ("id" if "id" in df.columns else None)
    if key is None:
        raise ValueError("Hittar varken 'transaction_id' eller 'id' i transaktionsfilen.")
    df = df.drop_duplicates(subset=[key], keep="first")
    print(f"Efter drop_duplicates på {key}: {len(df)}")

    out = OUT_DIR / "transactions_clean.csv"
    df.to_csv(out, index=False)
    print(f"\nTransaktionsdata sparad i {out}\n")

    return df


def flag_suspected_transactions(df_tx: pd.DataFrame):
    # Konfig som matchar din nuvarande risk_rules.RiskConfig
    from risk_rules import RiskConfig, score_and_flag

    cfg = RiskConfig(
        # Bas
        high_amount_p=0.98,
        crossborder_p=0.98,
        structuring_by_currency={
            "SEK": (9500, 9999.99),
            "EUR": (950, 999.99),
            "USD": (950, 999.99),
        },
        keyword_list=("crypto", "urgent"),

        # Kombinationslogik
        require_high_for_keyword=True,
        require_high_for_crossborder=True,
        exclude_structuring_from_crossborder=True,

        # Avancerat
        velocity_window_hours=24,
        velocity_min_tx=20,
        pingpong_days=7,
        pingpong_min_pairs=1,
        new_counterparty_days=14,
        require_high_for_new_counterparty=True,

        # Failsafe (valfritt – börja utan)
        # cap_per_reason=3000,
    )

    flagged = score_and_flag(df_tx, cfg=cfg)
    out = OUT_DIR / "flagged_transactions.csv"
    flagged.to_csv(out, index=False)

    print("\nFlaggade transaktioner sparade i data/clean/flagged_transactions.csv")
    print(f"Antal flaggade: {len(flagged)}")
    if len(flagged):
        print("Exempel (topp 5):")
        print(flagged.head(5).to_string(index=False))


if __name__ == "__main__":
    clean_customers()
    tx = clean_transactions()
    flag_suspected_transactions(tx)
