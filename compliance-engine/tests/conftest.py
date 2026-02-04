"""
Pytest configuration and shared fixtures.
"""

import asyncio
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Add src directory to Python path
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
async def reset_database():
    """Reset database before each test."""
    from app.storage.db import engine, Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield

    # Cleanup after test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session():
    """Provide a database session for tests."""
    from app.storage.db import get_session

    async for session in get_session():
        yield session


@pytest.fixture
def client():
    """Provide a FastAPI test client."""
    from app.main import app

    return TestClient(app)
