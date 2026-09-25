from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="GEONET_", extra="ignore")

    environment: Literal["development", "test"] = "development"
    postgres_host: str = "postgres"
    postgres_port: int = Field(default=5432, ge=1, le=65535)
    postgres_db: str = "geonet"
    postgres_user: str = "geonet"
    postgres_password: SecretStr = Field(min_length=16)
    redis_url: str = "redis://redis:6379/0"
    s3_endpoint: str = "http://minio:9000"
    s3_access_key: SecretStr = Field(min_length=3)
    s3_secret_key: SecretStr = Field(min_length=16)
    s3_bucket: str = "geonet-evidence"
    cors_origins: list[str] = ["http://localhost:3000"]
    allowed_hosts: list[str] = ["localhost", "127.0.0.1", "api", "testserver"]
