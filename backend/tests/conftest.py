import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import Settings


@pytest.fixture(scope="session")
def settings() -> Settings:
    s = Settings()
    if not s.test_database_url:
        pytest.skip("TEST_DATABASE_URL not configured")
    return s


@pytest.fixture(scope="session")
def test_engine(settings: Settings):
    engine = create_engine(settings.test_database_url, pool_pre_ping=True)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(test_engine):
    connection = test_engine.connect()
    transaction = connection.begin()
    SessionLocal = sessionmaker(bind=connection, autocommit=False, autoflush=False)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(test_engine) -> TestClient:
    os.environ["DATABASE_URL"] = str(test_engine.url)
    from app.db import session as db_session_module
    from app.main import app

    original_engine = db_session_module.engine
    db_session_module.engine = test_engine
    db_session_module.SessionLocal.configure(bind=test_engine)
    try:
        with TestClient(app) as c:
            yield c
    finally:
        db_session_module.engine = original_engine
        db_session_module.SessionLocal.configure(bind=original_engine)
