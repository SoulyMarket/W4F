from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Local/native dev runs from backend/, so the repo-root .env (the one
    # docker-compose also uses) is found via "../.env"; ".env" covers running
    # from the repo root instead. Inside Docker, compose injects real env
    # vars directly and no file is needed.
    model_config = SettingsConfigDict(env_file=(".env", "../.env"), extra="ignore")

    env: str = "dev"

    database_url: str
    test_database_url: str | None = None

    jwt_secret: str
    access_token_expire_minutes: int = 15
    refresh_token_expire_days_moqaddem: int = 30
    refresh_token_expire_days_other: int = 7

    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "w4f"
    minio_secret_key: str = "change-me"
    minio_bucket: str = "w4f-media"
    minio_secure: bool = False

    cors_origins_csv: str = Field(default="", validation_alias="CORS_ORIGINS")

    fcm_credentials_json: str = ""

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.cors_origins_csv.split(",") if o.strip()]

    @property
    def docs_enabled(self) -> bool:
        return self.env == "dev"
