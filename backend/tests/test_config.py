from app.core.config import Settings


def test_settings_reads_from_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@h:5432/d")
    monkeypatch.setenv("JWT_SECRET", "s3cret")
    monkeypatch.setenv("ENV", "dev")
    settings = Settings()
    assert settings.database_url == "postgresql+psycopg://u:p@h:5432/d"
    assert settings.jwt_secret == "s3cret"
    assert settings.env == "dev"


def test_settings_defaults(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@h:5432/d")
    monkeypatch.setenv("JWT_SECRET", "s3cret")
    settings = Settings()
    assert settings.access_token_expire_minutes == 15
    assert settings.refresh_token_expire_days_moqaddem == 30
    assert settings.refresh_token_expire_days_other == 7
    assert settings.env == "dev"


def test_cors_origins_parsed_as_list(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@h:5432/d")
    monkeypatch.setenv("JWT_SECRET", "s3cret")
    monkeypatch.setenv("CORS_ORIGINS", "http://a.com,http://b.com")
    settings = Settings()
    assert settings.cors_origins == ["http://a.com", "http://b.com"]


def test_openapi_only_enabled_in_dev(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@h:5432/d")
    monkeypatch.setenv("JWT_SECRET", "s3cret")
    monkeypatch.setenv("ENV", "production")
    settings = Settings()
    assert settings.docs_enabled is False

    monkeypatch.setenv("ENV", "dev")
    settings = Settings()
    assert settings.docs_enabled is True
