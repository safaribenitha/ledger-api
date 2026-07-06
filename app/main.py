from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from decimal import Decimal

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Base, engine, get_session
from app.models import Account, Transaction
from app.schemas import AccountCreate, AccountRead, BalanceRead, TransferCreate, TransferRead


router = APIRouter()
_account_locks: dict[str, asyncio.Lock] = {}
_account_locks_guard = asyncio.Lock()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


def create_app() -> FastAPI:
    application = FastAPI(title="Multi-Currency Ledger API", version="1.0.0", lifespan=lifespan)
    application.include_router(router)
    return application


async def _locks_for_accounts(*account_ids: str) -> list[asyncio.Lock]:
    unique_ids = sorted(set(account_ids))
    async with _account_locks_guard:
        return [_account_locks.setdefault(account_id, asyncio.Lock()) for account_id in unique_ids]


@asynccontextmanager
async def _locked_accounts(*account_ids: str) -> AsyncIterator[None]:
    locks = await _locks_for_accounts(*account_ids)
    for lock in locks:
        await lock.acquire()
    try:
        yield
    finally:
        for lock in reversed(locks):
            lock.release()


async def _get_account_for_update(session: AsyncSession, account_id: str) -> Account:
    result = await session.execute(
        select(Account).where(Account.id == account_id).with_for_update()
    )
    account = result.scalar_one_or_none()
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return account


@router.post("/accounts", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
async def create_account(payload: AccountCreate, session: AsyncSession = Depends(get_session)) -> Account:
    account = Account(
        user_id=payload.user_id,
        currency=payload.currency,
        balance=payload.initial_balance,
    )
    session.add(account)
    await session.commit()
    await session.refresh(account)
    return account


@router.get("/accounts/{account_id}/balance", response_model=BalanceRead)
async def read_account_balance(account_id: str, session: AsyncSession = Depends(get_session)) -> BalanceRead:
    account = await session.get(Account, account_id)
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return BalanceRead(account_id=account.id, currency=account.currency, balance=account.balance)


@router.get("/balance", response_model=BalanceRead)
async def read_balance(
    account_id: str = Query(min_length=1),
    session: AsyncSession = Depends(get_session),
) -> BalanceRead:
    return await read_account_balance(account_id=account_id, session=session)


@router.post("/transfers", response_model=TransferRead, status_code=status.HTTP_201_CREATED)
async def create_transfer(payload: TransferCreate, session: AsyncSession = Depends(get_session)) -> Transaction:
    if payload.from_account_id == payload.to_account_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Source and destination accounts must be different",
        )

    async with _locked_accounts(payload.from_account_id, payload.to_account_id):
        async with session.begin():
            source = await _get_account_for_update(session, payload.from_account_id)
            destination = await _get_account_for_update(session, payload.to_account_id)

            if source.currency != payload.currency or destination.currency != payload.currency:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Transfer currency must match both account currencies",
                )
            if source.balance < payload.amount:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Insufficient funds",
                )

            source.balance = Decimal(source.balance) - payload.amount
            destination.balance = Decimal(destination.balance) + payload.amount
            transaction = Transaction(
                from_account_id=source.id,
                to_account_id=destination.id,
                currency=payload.currency,
                amount=payload.amount,
                status="posted",
            )
            session.add(transaction)

    await session.refresh(transaction)
    return transaction


app = create_app()
