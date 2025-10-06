import pytest
from sqlalchemy import text
from init_schema import ensure_schema
from import_customers import main as import_customers_main
from import_transactions import main as import_transactions_main
from import_flagged_transactions import main as import_flagged_main

@pytest.mark.db
@pytest.mark.integration
def test_import_end_to_end(tmp_path, db_engine, ensure_db, monkeypatch):
    data_dir = tmp_path / "data" / "clean"
    data_dir.mkdir(parents=True, exist_ok=True)

    (data_dir / "customers_clean.csv").write_text(
        "Customer,Personnummer,BankAccount,Address,Phone\n"
        "Alice,010101-1237,ACC1,Gatan 1,+461234\n"
        "Bob,990101-5678,ACC2,Gatan 2,+461111\n",
        encoding="utf-8"
    )
    (data_dir / "transactions_clean.csv").write_text(
        "id,timestamp,amount,currency,sender_acc,receiver_acc,sender_country,receiver_country,transaction_type,notes\n"
        "T100,2025-01-01 00:00:00,100.0,SEK,ACC1,ACC2,Sweden,Sweden,outgoing,test\n",
        encoding="utf-8"
    )
    (data_dir / "flagged_transactions.csv").write_text(
        "transaction_id,reason,flagged_date,amount\n"
        "T100,High amount vs p98 (per valuta),2025-10-05,100.0\n",
        encoding="utf-8"
    )

    import import_customers as ic
    import import_transactions as itx
    import import_flagged_transactions as ift

    monkeypatch.setattr(ic, "CUSTOMERS_CSV", str(data_dir / "customers_clean.csv"))
    monkeypatch.setattr(itx, "TX_CSV", str(data_dir / "transactions_clean.csv"))
    monkeypatch.setattr(ift, "FLAGGED_CSV", str(data_dir / "flagged_transactions.csv"))

    ensure_schema()
    import_customers_main()
    import_transactions_main()
    import_flagged_main()

    with db_engine.begin() as conn:
        assert conn.execute(text("SELECT COUNT(*) FROM bank.customers")).scalar_one() >= 2
        assert conn.execute(text("SELECT COUNT(*) FROM bank.accounts")).scalar_one() >= 2
        assert conn.execute(text("SELECT COUNT(*) FROM bank.transactions")).scalar_one() >= 1
        assert conn.execute(text("SELECT COUNT(*) FROM bank.flagged_transactions")).scalar_one() >= 1