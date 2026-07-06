from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def new_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, index=True)
    balance: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    outgoing_transactions: Mapped[list[Transaction]] = relationship(
        back_populates="from_account",
        foreign_keys="Transaction.from_account_id",
    )
    incoming_transactions: Mapped[list[Transaction]] = relationship(
        back_populates="to_account",
        foreign_keys="Transaction.to_account_id",
    )


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    from_account_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("accounts.id", ondelete="RESTRICT"),
        nullable=False,
    )
    to_account_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("accounts.id", ondelete="RESTRICT"),
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="posted")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    from_account: Mapped[Account] = relationship(
        back_populates="outgoing_transactions",
        foreign_keys=[from_account_id],
    )
    to_account: Mapped[Account] = relationship(
        back_populates="incoming_transactions",
        foreign_keys=[to_account_id],
    )


Index("ix_transactions_from_account_created_at", Transaction.from_account_id, Transaction.created_at)
Index("ix_transactions_to_account_created_at", Transaction.to_account_id, Transaction.created_at)
