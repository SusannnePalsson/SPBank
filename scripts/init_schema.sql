import os
from sqlalchemy import create_engine, text
from db import Base, engine

SQL_FILE = os.path.join(os.path.dirname(__file__), "create_bank_schema.sql")

def run_sql_file(engine, filename):
    """Kör SQL-fil direkt mot databasen."""
    with engine.begin() as conn:
        with open(filename, "r", encoding="utf-8") as f:
            sql_commands = f.read()
        for cmd in sql_commands.split(";"):
            cmd = cmd.strip()
            if cmd:
                conn.execute(text(cmd))

def ensure_schema():
    # Kör rå SQL först (skapar schema + tabeller)
    if os.path.exists(SQL_FILE):
        print(f"✅ Kör SQL från {SQL_FILE}")
        run_sql_file(engine, SQL_FILE)
    else:
        print("⚠️ Ingen SQL-fil hittad, hoppar över rå SQL.")

    # Säkerställ att SQLAlchemy-tabeller också finns
    print("✅ Säkerställer SQLAlchemy-tabeller...")
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    ensure_schema()
    print("✅ Schema och tabeller skapade!")
