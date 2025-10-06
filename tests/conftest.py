import os
import sys
import pathlib
import pytest
from sqlalchemy import text, create_engine
from importlib import import_module

# Säkerställ att projektroten finns i sys.path när testerna körs från annan katalog
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

# Använd projektets db.py om möjligt, annars fall-back till env
try:
    db = import_module("db")
    engine = db.engine
except Exception:
    # Fallback: läs DATABASE_URL direkt
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/postgres")
    # Sätt search_path bank,public om ej angivet
    if "options=" not in DATABASE_URL:
        sep = "&" if "?" in DATABASE_URL else "?"
        DATABASE_URL = f"{DATABASE_URL}{sep}options=-csearch_path%3Dbank%2Cpublic"
    engine = create_engine(DATABASE_URL, future=True)

@pytest.fixture(scope="session")
def db_engine():
    return engine

@pytest.fixture(scope="session")
def ensure_db(db_engine):
    try:
        with db_engine.connect() as c:
            c.execute(text("SELECT 1"))
    except Exception as e:
        pytest.skip(f"Hoppar DB-relaterade tester: kunde inte ansluta till databasen ({e})")

def pytest_sessionfinish(session, exitstatus):
    tr = session.config.pluginmanager.get_plugin("terminalreporter")
    if not tr:
        return
    messages = {
        0: "✅ Alla tester passerade!",
        1: "❌ Tester misslyckades.",
        2: "⏹️ Avbrutet av användaren.",
        3: "⚠️ Internt pytest-fel.",
        4: "⚠️ Användningsfel.",
        5: "ℹ️ Inga tester hittades."
    }
    tr.write_line("\n" + messages.get(exitstatus, f"Exitstatus: {exitstatus}") + "\n")
