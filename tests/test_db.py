import pytest
from sqlalchemy import text, inspect
from init_schema import ensure_schema

@pytest.mark.db
def test_can_connect_select1(db_engine, ensure_db):
    with db_engine.connect() as c:
        res = c.execute(text("SELECT 1")).scalar_one()
        assert res == 1

@pytest.mark.db
def test_ensure_schema_and_tables_exist(db_engine, ensure_db):
    ensure_schema()
    insp = inspect(db_engine)
    tables = set(insp.get_table_names(schema="bank"))
    expected = {"customers", "accounts", "transactions", "flagged_transactions"}
    missing = expected - tables
    assert not missing, f"Saknade tabeller i schema 'bank': {missing}"