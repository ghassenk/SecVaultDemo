"""
Pytest configuration and shared fixtures.

Sets up test database with proper isolation between tests.
"""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
    AsyncEngine,
)

from app.core.config import get_settings
from app.core.database import Base, get_db

settings = get_settings()


@pytest.fixture(scope="session")
async def engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create the test database engine."""
    engine = create_async_engine(
        settings.database_url,
        echo=False,
        pool_pre_ping=True,
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Drop tables and dispose
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture(scope="session")
def session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Create session factory bound to test engine."""
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )


@pytest.fixture
async def db_session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional database session for tests."""
    async with session_factory() as session:
        yield session
        # Rollback any uncommitted changes
        await session.rollback()


@pytest.fixture
async def client(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client with overridden database dependency."""
    from app.main import create_application
    
    # Create a fresh app instance
    app = create_application()
    
    # Override the get_db dependency
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture(autouse=True)
async def clean_tables(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[None, None]:
    """Clean all tables after each test for isolation."""
    yield
    async with session_factory() as session:
        # Delete in correct order due to foreign keys
        await session.execute(text("DELETE FROM secrets"))
        await session.execute(text("DELETE FROM users"))
        await session.commit()


@pytest.fixture
async def authenticated_client(
    client: AsyncClient,
) -> AsyncGenerator[tuple[AsyncClient, str], None]:
    """Create an authenticated client with a test user."""
    user_data = {
        "email": "authenticated@example.com",
        "password": "SecureP@ssw0rd123!",
    }
    
    # Register user
    await client.post("/api/v1/auth/register", json=user_data)
    
    # Login and get token
    response = await client.post("/api/v1/auth/login", json=user_data)
    token = response.json()["access_token"]
    
    yield client, token
    