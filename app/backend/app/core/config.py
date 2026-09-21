# Ref: BL-QA-001 | Skill: K-004 | Fase: F5
# Ref: BL-O1-* | Skill: K-014 | Fase: F6
# Ref: A04 | ADR-009
"""Application settings loaded from environment (.env)."""

from functools import lru_cache
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for SIGA local environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    app_name: str = "SIGA"
    app_env: str = "local"
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    app_debug: bool = True
    app_api_prefix: str = "/api/v1"

    db_host: str = "127.0.0.1"
    db_port: int = 3306
    db_name: str = "siga"
    db_user: str = "root"
    db_password: str = ""
    db_driver: str = "mysql+pymysql"
    database_url_override: Optional[str] = Field(default=None, alias="DATABASE_URL")

    jwt_secret: str = Field(default="CHANGE_ME_GENERATE_A_LONG_RANDOM_SECRET_32PLUS")
    jwt_algorithm: str = "HS256"
    jwt_access_ttl_minutes: int = 30
    jwt_refresh_ttl_days: int = 7

    password_hasher: str = "argon2"

    log_level: str = "INFO"
    log_dir: str = "logs"

    policy_path: str = "policies/v1"

    ai_provider: str = "mock"
    ai_api_key: str = ""
    ai_base_url: str = ""
    ai_model: str = ""

    cors_origins: str = (
        "http://127.0.0.1:8000,http://localhost:8000,"
        "http://127.0.0.1:5500,http://localhost:5500"
    )

    @property
    def database_url(self) -> str:
        if self.database_url_override:
            return self.database_url_override
        password = self.db_password or ""
        auth = f"{self.db_user}:{password}@" if password else f"{self.db_user}@"
        return (
            f"{self.db_driver}://{auth}{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_jwt_secret_default(self) -> bool:
        return self.jwt_secret.startswith("CHANGE_ME")


@lru_cache
def get_settings() -> Settings:
    return Settings()
