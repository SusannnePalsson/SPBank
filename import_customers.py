
import pandas as pd
from sqlalchemy import text
from db import engine

CUSTOMERS_CSV = "data/clean/customers_clean.csv"

def main():
    df = pd.read_csv(CUSTOMERS_CSV, dtype=str, keep_default_na=False).rename(
        columns={
            "Customer":"customer",
            "Personnummer":"personnummer",
            "BankAccount":"account_number",
            "Address":"address",
            "Phone":"phone"
        }
    )
    inserted_customers = skipped_customers = 0
    inserted_accounts = skipped_accounts = missing_owner = 0

    sql_customer = text("""
        INSERT INTO bank.customers (customer, personnummer, address, phone)
        VALUES (:customer, :personnummer, NULLIF(:address,''), NULLIF(:phone,''))
        ON CONFLICT (personnummer) DO NOTHING
    """)

    sql_account = text("""
        INSERT INTO bank.accounts (account_number, customer_id, balance)
        SELECT :account_number, c.id, COALESCE(:balance, 0)
        FROM bank.customers c
        WHERE c.personnummer = :personnummer
        ON CONFLICT (account_number) DO NOTHING
    """)

    with engine.begin() as conn:
        for _, row in df.iterrows():
            # customers
            rc = conn.execute(sql_customer, dict(
                customer=row.get("customer","").strip(),
                personnummer=row.get("personnummer","").strip(),
                address=row.get("address","").strip(),
                phone=row.get("phone","").strip(),
            )).rowcount
            if rc: inserted_customers += 1
            else: skipped_customers += 1

            # accounts
            if row.get("account_number"):
                rc = conn.execute(sql_account, dict(
                    account_number=row["account_number"].strip(),
                    personnummer=row.get("personnummer","").strip(),
                    balance=0.0
                )).rowcount
                if rc: inserted_accounts += 1
                else:
                    exists = conn.execute(
                        text("SELECT 1 FROM bank.customers WHERE personnummer=:pn LIMIT 1"),
                        {"pn": row.get("personnummer","").strip()}
                    ).first()
                    if exists: skipped_accounts += 1
                    else: missing_owner += 1

    print(f"[customers] inserted={inserted_customers}, skipped_existing={skipped_customers}")
    print(f"[accounts ] inserted={inserted_accounts}, skipped_existing={skipped_accounts}, missing_owner={missing_owner}")

if __name__ == "__main__":
    main()
