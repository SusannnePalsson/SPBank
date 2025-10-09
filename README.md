
# SPBank

Ett komplett, fungerande ETL-projekt (CSV → validering → Postgres) med Prefect-orkestrering och DB-hantering i lokal PostgreSQL databas bank via pgAdmin med schemat **bank**.

## Struktur
```
SPBank/
├─ data/
│  ├─ sebank_customers_with_accounts.csv     # Alla kunder med konto
│  ├─ transactions.csv                       # Alla transakttioner
│  └─ clean/                                 # Rensade filerna
├─ scripts/
│  └─ init_schema.sql
├─ db.py
├─ models.py
├─ init_schema.py
├─ validation.py
├─ import_customers.py
├─ import_transactions.py
├─ import_flagged_transactions.py
├─ flow_main.py
├─ requirements.txt
├─ docker-compose.yml
└─ .env.example
```

## Snabbstart (Windows / PowerShell)
1. **Lägg CSV-filerna** i `data/`:
   - `data/sebank_customers_with_accounts.csv`
   - `data/transactions.csv`

2. **Starta Postgres + pgAdmin via Docker (Jag kör lokal databas inte Docker) **:
   ```powershell
   docker compose up -d
   ```
   - pgAdmin: http://localhost:5050 (admin@example.com / admin)
   - DB i pgAdmin:
     - Host: `db` (från pgAdmin i container), eller `localhost` från din dator
     - Port: `5432`
     - User: `bankuser`
     - Pass: `bankpass`
     - DB:   `bankdb`

3. **Skapa venv & installera**:
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate
   pip install -r requirements.txt
   Copy-Item .env.example .env
   ```

4. **Kör hela ETL**:
   ```powershell
   python flow_main.py
   ```

5. **Verifiera i Postgres** (jag kör via pgAdmin):
   ```sql
   SELECT count(*) FROM bank.customers;
   SELECT count(*) FROM bank.accounts;
   SELECT count(*) FROM bank.transactions;
   SELECT count(*) FROM bank.flagged_transactions;
   ```

## Vad körs?
- `init_schema.py` säkerställer schema **bank** + alla tabeller (SQLAlchemy modeller i `models.py`).  
- `validation.py` bygger cleanade CSV i `data/clean/`.  
- `import_*.py` laddar in data med `ON CONFLICT DO NOTHING` och loggar:
  - `inserted`, `skipped_existing`, och ev. `missing_*` orsaker.
- `flow_main.py` (Prefect) kör alla steg i ordning och skriver en **sammanfattning**.

## Konfiguration
- Ändra anslutning i `.env` om du inte använder Docker-standarden:
  ```ini
  DATABASE_URL=postgresql+psycopg://USER:PASS@HOST:5432/DBNAME
  ```
  `db.py` lägger automatiskt till `search_path=bank,public`.

## Tester
Projektet har `pytest` för tester.
```powershell
python -m pytest -q
```


