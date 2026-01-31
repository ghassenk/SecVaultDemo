"""
Pytest configuration and shared fixtures.

Uses async tests with proper event loop configuration.
"""

import pytest
from collections.abc import AsyncGenerator
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
from app.core import database as db_module
from app.main import app
from app.core.security import limiter

settings = get_settings()


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create the test database engine for each test."""
    # Reset global engine to avoid cross-test contamination
    db_module._engine = None
    db_module._async_session_maker = None
    
    engine = create_async_engine(
        settings.database_url,
        echo=False,
        pool_pre_ping=True,
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    await engine.dispose()


@pytest.fixture
async def session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
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
    """Provide a database session for tests."""
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(
    request: pytest.FixtureRequest,
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client with overridden database dependency."""
    
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


@pytest.fixture
async def authenticated_client(
    client: AsyncClient,
) -> AsyncGenerator[tuple[AsyncClient, str], None]:
    """Create an authenticated client with a test user."""
    user_data = {
        "email": "authenticated@example.com",
        "password": "SecureP@ssw0rd123!",
    }
    
    await client.post("/api/v1/auth/register", json=user_data)
    response = await client.post("/api/v1/auth/login", json=user_data)
    token = response.json()["access_token"]
    
    yield client, token

@pytest.fixture(autouse=True)
def disable_rate_limiter_for_marked_tests(request):
    """
    Automatically checks if a test has the @pytest.mark.no_ratelimit marker.
    If so, it disables the limiter for that specific test.
    """
    # Check if the marker exists on the test function
    marker = request.node.get_closest_marker("no_ratelimit")
    
    if marker:
        # Store previous state just in case (usually True)
        previous_state = limiter.enabled
        
        # Disable the limiter
        limiter.enabled = False
        
        yield  # Run the test
        
        # Re-enable the limiter after the test finishes
        limiter.enabled = previous_state
    else:
        yield
