import os
from pathlib import Path
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_database_url() -> str:
    explicit_data_dir = os.environ.get("NETATLAS_DATA_DIR")
    if explicit_data_dir:
        data_dir = Path(explicit_data_dir)
    else:
        data_dir = Path("./storage")

    return f"sqlite:///{(data_dir / 'netatlas.db').as_posix()}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    api_prefix: str = Field(default="/api", alias="API_PREFIX")
    database_url: str = Field(default_factory=_default_database_url, alias="DATABASE_URL")
    https_enabled: bool = Field(default=False, alias="HTTPS_ENABLED")
    https_port: int = Field(default=8443, alias="HTTPS_PORT")
    https_cert_file: str | None = Field(default=None, alias="HTTPS_CERT_FILE")
    https_key_file: str | None = Field(default=None, alias="HTTPS_KEY_FILE")
    syslog_enabled: bool = Field(default=True, alias="SYSLOG_ENABLED")
    syslog_bind_host: str = Field(default="0.0.0.0", alias="SYSLOG_BIND_HOST")
    syslog_bind_port: int = Field(default=5140, alias="SYSLOG_BIND_PORT")
    syslog_max_message_size: int = Field(default=65535, alias="SYSLOG_MAX_MESSAGE_SIZE")
    wan_interface_keywords: str = Field(default="wan,internet,pppoe", alias="WAN_INTERFACE_KEYWORDS")
    geoip_lookup_enabled: bool = Field(default=True, alias="GEOIP_LOOKUP_ENABLED")
    geoip_lookup_url: str = Field(default="https://ipwho.is/{ip}", alias="GEOIP_LOOKUP_URL")
    geoip_lookup_timeout_seconds: float = Field(default=3.0, alias="GEOIP_LOOKUP_TIMEOUT_SECONDS")
    cors_origins: str = Field(default="http://localhost:5173", alias="CORS_ORIGINS")

    @property
    def wan_keywords(self) -> list[str]:
        return [part.strip().lower() for part in self.wan_interface_keywords.split(",") if part.strip()]

    @property
    def cors_origin_list(self) -> list[str]:
        return [part.strip() for part in self.cors_origins.split(",") if part.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
