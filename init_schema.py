from sqlalchemy import text
from db import engine
from models import Base

def ensure_schema():
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS bank"))
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    ensure_schema()
    print("✅ Schema 'bank' och alla tabeller är på plats.")