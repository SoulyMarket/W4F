import os
import socket
import subprocess
import sys
import time

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


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def moto_s3_endpoint():
    """A local moto_server instance speaking the S3 API, standing in for
    MinIO: Docker can't run on this dev machine and MinIO's winget package
    currently has a broken upstream manifest (see PROGRESS.md). Same
    boto3-facing surface (presigned PUT/GET, head_object) as real MinIO —
    only the endpoint changes, via the MINIO_* env vars this fixture sets
    before any Settings() is constructed by a request.
    """
    port = _free_port()
    endpoint = f"127.0.0.1:{port}"
    proc = subprocess.Popen(
        [sys.executable, "-m", "moto.server", "-H", "127.0.0.1", "-p", str(port)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        for _ in range(50):
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                    break
            except OSError:
                time.sleep(0.1)
        else:
            raise RuntimeError("moto_server did not start in time")

        os.environ["MINIO_ENDPOINT"] = endpoint
        os.environ["MINIO_SECURE"] = "false"
        os.environ["MINIO_ACCESS_KEY"] = "test"
        os.environ["MINIO_SECRET_KEY"] = "test"
        os.environ["MINIO_BUCKET"] = "w4f-media-test"

        from app.services.storage import get_s3_client

        client = get_s3_client(Settings())
        client.create_bucket(Bucket="w4f-media-test")

        yield endpoint
    finally:
        proc.terminate()
        proc.wait(timeout=5)


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
