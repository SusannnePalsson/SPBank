-- Skapa schema om det inte finns
CREATE SCHEMA IF NOT EXISTS bank AUTHORIZATION postgres;

-- Customers
CREATE TABLE IF NOT EXISTS bank.customers (
    id SERIAL PRIMARY KEY,
    customer VARCHAR(255) NOT NULL,
    personnummer VARCHAR(20) UNIQUE NOT NULL,
    phone VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Accounts
CREATE TABLE IF NOT EXISTS bank.accounts (
    id SERIAL PRIMARY KEY,
    account_number VARCHAR(64) UNIQUE NOT NULL,
    customer_id INTEGER NOT NULL REFERENCES bank.customers(id) ON DELETE CASCADE,
    balance NUMERIC(18,2) DEFAULT 0.0
);

-- Transactions
CREATE TABLE IF NOT EXISTS bank.transactions (
    id VARCHAR(128) PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    amount NUMERIC(18,2) NOT NULL,
    currency VARCHAR(10) NOT NULL,
    notes TEXT,
    sender_account_id INTEGER REFERENCES bank.accounts(id),
    receiver_account_id INTEGER REFERENCES bank.accounts(id),
    sender_country VARCHAR(100),
    sender_municipality VARCHAR(100),
    receiver_country VARCHAR(100),
    receiver_municipality VARCHAR(100),
    transaction_type VARCHAR(50)
);

-- Flagged transactions
CREATE TABLE IF NOT EXISTS bank.flagged_transactions (
    id SERIAL PRIMARY KEY,
    transaction_id VARCHAR(128) NOT NULL REFERENCES bank.transactions(id) ON DELETE CASCADE,
    reason TEXT NOT NULL,
    flagged_date DATE DEFAULT CURRENT_DATE,
    amount NUMERIC(18,2)
);

-- Indexer
CREATE INDEX IF NOT EXISTS ix_accounts_customer_id ON bank.accounts(customer_id);
CREATE INDEX IF NOT EXISTS ix_transactions_sender_account_id ON bank.transactions(sender_account_id);
CREATE INDEX IF NOT EXISTS ix_transactions_receiver_account_id ON bank.transactions(receiver_account_id);
CREATE INDEX IF NOT EXISTS ix_flagged_tx_id ON bank.flagged_transactions(transaction_id);
