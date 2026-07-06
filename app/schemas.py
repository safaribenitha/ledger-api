from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


Currency = Literal["USD", "EUR", "PLN"]
MONEY_QUANT = Decimal("0.01")


def quantize_money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


class AccountCreate(BaseModel):
    user_id: str = Field(min_length=1, max_length=128)
    currency: Currency
    initial_balance: Decimal = Field(ge=Decimal("0.00"), max_digits=18, decimal_places=2)

    @field_validator("initial_balance")
    @classmethod
    def normalize_initial_balance(cls, value: Decimal) -> Decimal:
        return quantize_money(value)


class AccountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    currency: Currency
    balance: Decimal


class BalanceRead(BaseModel):
    account_id: str
    currency: Currency
    balance: Decimal


class TransferCreate(BaseModel):
    from_account_id: str = Field(min_length=1)
    to_account_id: str = Field(min_length=1)
    currency: Currency
    amount: Decimal = Field(gt=Decimal("0.00"), max_digits=18, decimal_places=2)

    @field_validator("amount")
    @classmethod
    def normalize_amount(cls, value: Decimal) -> Decimal:
        return quantize_money(value)


class TransferRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    from_account_id: str
    to_account_id: str
    currency: Currency
    amount: Decimal
    status: str
