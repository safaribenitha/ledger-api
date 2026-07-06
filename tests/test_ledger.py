from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.anyio


def unique_user(prefix: str = "user") -> str:
    return f"{prefix}-{uuid4()}"


def money(value: str | int) -> str:
    return str(Decimal(str(value)).quantize(Decimal("0.01")))


async def create_account(
    client: AsyncClient,
    *,
    currency: str = "USD",
    initial_balance: str = "100.00",
    user_id: str | None = None,
) -> dict:
    response = await client.post(
        "/accounts",
        json={
            "user_id": user_id or unique_user(),
            "currency": currency,
            "initial_balance": initial_balance,
        },
    )
    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload["id"]
    assert payload["currency"] == currency
    assert Decimal(str(payload["balance"])) == Decimal(initial_balance)
    return payload


async def get_balance(client: AsyncClient, account_id: str) -> Decimal:
    response = await client.get(f"/accounts/{account_id}/balance")
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["account_id"] == account_id
    return Decimal(str(payload["balance"]))


async def transfer(
    client: AsyncClient,
    *,
    from_account_id: str,
    to_account_id: str,
    amount: str,
    currency: str = "USD",
):
    return await client.post(
        "/transfers",
        json={
            "from_account_id": from_account_id,
            "to_account_id": to_account_id,
            "currency": currency,
            "amount": amount,
        },
    )


@pytest.mark.parametrize("currency", ["USD", "EUR", "PLN"])
async def test_create_user_account_with_currency_balance(client: AsyncClient, currency: str) -> None:
    account = await create_account(
        client,
        currency=currency,
        initial_balance="1234.56",
        user_id=unique_user(currency.lower()),
    )

    assert account["user_id"].startswith(currency.lower())
    assert account["currency"] == currency
    assert Decimal(str(account["balance"])) == Decimal("1234.56")


async def test_check_account_balance(client: AsyncClient) -> None:
    account = await create_account(client, currency="EUR", initial_balance="250.75")

    balance = await get_balance(client, account["id"])

    assert balance == Decimal("250.75")


async def test_transfer_funds_between_two_accounts(client: AsyncClient) -> None:
    source = await create_account(client, currency="USD", initial_balance="100.00")
    destination = await create_account(client, currency="USD", initial_balance="10.00")

    response = await transfer(
        client,
        from_account_id=source["id"],
        to_account_id=destination["id"],
        amount="25.50",
        currency="USD",
    )

    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload["from_account_id"] == source["id"]
    assert payload["to_account_id"] == destination["id"]
    assert Decimal(str(payload["amount"])) == Decimal("25.50")
    assert payload["currency"] == "USD"
    assert payload["status"] in {"posted", "completed", "success"}
    assert await get_balance(client, source["id"]) == Decimal("74.50")
    assert await get_balance(client, destination["id"]) == Decimal("35.50")


async def test_transfer_rejects_insufficient_funds(client: AsyncClient) -> None:
    source = await create_account(client, currency="USD", initial_balance="20.00")
    destination = await create_account(client, currency="USD", initial_balance="0.00")

    response = await transfer(
        client,
        from_account_id=source["id"],
        to_account_id=destination["id"],
        amount="20.01",
        currency="USD",
    )

    assert response.status_code == 409, response.text
    assert "insufficient" in response.text.lower()
    assert await get_balance(client, source["id"]) == Decimal("20.00")
    assert await get_balance(client, destination["id"]) == Decimal("0.00")


async def test_transfer_rejects_currency_mismatch(client: AsyncClient) -> None:
    source = await create_account(client, currency="USD", initial_balance="100.00")
    destination = await create_account(client, currency="EUR", initial_balance="0.00")

    response = await transfer(
        client,
        from_account_id=source["id"],
        to_account_id=destination["id"],
        amount="10.00",
        currency="USD",
    )

    assert response.status_code in {400, 409, 422}, response.text
    assert "currency" in response.text.lower()
    assert await get_balance(client, source["id"]) == Decimal("100.00")
    assert await get_balance(client, destination["id"]) == Decimal("0.00")


@pytest.mark.parametrize("amount", ["-0.01", "-10.00", "0.00"])
async def test_transfer_rejects_non_positive_amounts(client: AsyncClient, amount: str) -> None:
    source = await create_account(client, currency="PLN", initial_balance="100.00")
    destination = await create_account(client, currency="PLN", initial_balance="0.00")

    response = await transfer(
        client,
        from_account_id=source["id"],
        to_account_id=destination["id"],
        amount=amount,
        currency="PLN",
    )

    assert response.status_code == 422, response.text
    assert await get_balance(client, source["id"]) == Decimal("100.00")
    assert await get_balance(client, destination["id"]) == Decimal("0.00")


async def test_concurrent_withdrawals_cannot_double_spend(client: AsyncClient) -> None:
    source = await create_account(client, currency="USD", initial_balance="100.00")
    destination = await create_account(client, currency="USD", initial_balance="0.00")

    async def attempt_transfer():
        return await transfer(
            client,
            from_account_id=source["id"],
            to_account_id=destination["id"],
            amount="30.00",
            currency="USD",
        )

    responses = await asyncio_gather_compat(*(attempt_transfer() for _ in range(10)))
    successful = [response for response in responses if response.status_code == 201]
    rejected = [response for response in responses if response.status_code != 201]

    assert len(successful) == 3
    assert all(response.status_code == 409 for response in rejected), [
        (response.status_code, response.text) for response in rejected
    ]
    assert await get_balance(client, source["id"]) == Decimal("10.00")
    assert await get_balance(client, destination["id"]) == Decimal("90.00")


async def asyncio_gather_compat(*coroutines):
    import asyncio

    return await asyncio.gather(*coroutines)
