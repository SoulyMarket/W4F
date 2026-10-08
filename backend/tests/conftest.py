import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

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
    """One real connection + outer transaction per test, rolled back at the
    end no matter what. Route handlers call db.commit() in normal operation,
    so the session is bound with join_transaction_mode="create_savepoint":
    session.commit() then only releases a SAVEPOINT instead of ending the
    outer transaction — without this, the first route-level commit() would
    commit the outer transaction for real and the final rollback() would be
    a silent no-op, leaking every test's rows into the database permanently.
    """
    connection = test_engine.connect()
    transaction = connection.begin()
    SessionLocal = sessionmaker(
        bind=connection,
        autocommit=False,
        autoflush=False,
        join_transaction_mode="create_savepoint",
    )
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        if transaction.is_active:
            transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session: Session) -> TestClient:
    """A TestClient whose every request runs inside the SAME transaction as
    `db_session`, so a test can set up rows via direct ORM calls on
    `db_session` and then see them through the API, with everything rolled
    back together at the end — the standard FastAPI DB-testing pattern."""
    from app.db.session import get_db
    from app.main import app

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.dependency_overrides.pop(get_db, None)
