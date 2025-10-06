
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Numeric, Text, DateTime, ForeignKey, MetaData

# All tables live in schema "bank"
metadata = MetaData(schema="bank")

class Base(DeclarativeBase):
    metadata = metadata

class Customer(Base):
    __tablename__ = "customers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer: Mapped[str] = mapped_column(Text)
    personnummer: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)

class Account(Base):
    __tablename__ = "accounts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_number: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("bank.customers.id"), nullable=True)
    balance: Mapped[float | None] = mapped_column(Numeric(18,2), nullable=True, default=0)

class Transaction(Base):
    __tablename__ = "transactions"
    id: Mapped[str] = mapped_column(String(128), primary_key=True)  # CSV har str/uuid
    timestamp: Mapped["DateTime | None"] = mapped_column(DateTime, nullable=True)
    amount: Mapped[float | None] = mapped_column(Numeric(18,2), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(8), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    sender_account_id: Mapped[int | None] = mapped_column(ForeignKey("bank.accounts.id"), nullable=True)
    receiver_account_id: Mapped[int | None] = mapped_column(ForeignKey("bank.accounts.id"), nullable=True)
    sender_country: Mapped[str | None] = mapped_column(String(64), nullable=True)
    sender_municipality: Mapped[str | None] = mapped_column(String(128), nullable=True)
    receiver_country: Mapped[str | None] = mapped_column(String(64), nullable=True)
    receiver_municipality: Mapped[str | None] = mapped_column(String(128), nullable=True)
    transaction_type: Mapped[str | None] = mapped_column(String(64), nullable=True)

class FlaggedTransaction(Base):
    __tablename__ = "flagged_transactions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transaction_id: Mapped[str] = mapped_column(ForeignKey("bank.transactions.id", ondelete="CASCADE"))
    reason: Mapped[str] = mapped_column(Text)
    flagged_date: Mapped["DateTime | None"] = mapped_column(DateTime, nullable=True)
    amount: Mapped[float | None] = mapped_column(Numeric(18,2), nullable=True)
