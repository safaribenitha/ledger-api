import importlib
import os
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient


os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="session")
def app():
    """
    Expected application contract:
    - app.main exposes either `app` or `create_app()`.
    - the FastAPI app should read DATABASE_URL at startup.

    If the implementation exposes database dependency hooks, this fixture tries
    to override them with an isolated in-memory SQLite session.
    """
    main = importlib.import_module("app.main")
    fastapi_app = main.create_app() if hasattr(main, "create_app") else main.app

    try:
        database = importlib.import_module("app.database")
        from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
        from sqlalchemy.pool import StaticPool

        engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        metadata = None
        if hasattr(database, "Base"):
            metadata = database.Base.metadata
        elif hasattr(database, "SQLModel"):
            metadata = database.SQLModel.metadata

        fastapi_app.state.test_engine = engine
        fastapi_app.state.test_metadata = metadata

        async def override_session() -> AsyncIterator[object]:
            async with session_factory() as session:
                yield session

        for dependency_name in ("get_session", "get_db", "get_async_session"):
            dependency = getattr(database, dependency_name, None)
            if dependency is not None:
                fastapi_app.dependency_overrides[dependency] = override_session
    except ModuleNotFoundError:
        pass

    return fastapi_app


@pytest.fixture
async def client(app) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    test_engine = getattr(app.state, "test_engine", None)
    test_metadata = getattr(app.state, "test_metadata", None)

    if test_engine is not None and test_metadata is not None:
        async with test_engine.begin() as conn:
            await conn.run_sync(test_metadata.create_all)

    try:
        async with app.router.lifespan_context(app):
            async with AsyncClient(transport=transport, base_url="http://testserver") as test_client:
                yield test_client
    finally:
        if test_engine is not None and test_metadata is not None:
            async with test_engine.begin() as conn:
                await conn.run_sync(test_metadata.drop_all)
