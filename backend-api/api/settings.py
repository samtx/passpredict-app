from pathlib import Path
from typing import Literal

from pydantic import BaseModel, SecretStr, Field
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)


class DbConfig(BaseModel):
    url: str = "sqlite+aiosqlite:///./ppapi.db"
    echo: bool = False


class SpacetrackConfig(BaseModel):
    username: str = ""
    password: SecretStr = ""


class HatchetConfig(BaseModel):
    token: SecretStr = ""
    tenant_id: str = ""
    tls: Literal["none", "tls", "mtls"] = "none"
    namespace: str = ""
    debug: bool = False


class LoggingConfig(BaseModel):
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "WARNING"
    filename: Path = Path("api.log")


class PredictConfig(BaseModel):
    dt_seconds: int = 1
    max_days: int = 10
    max_satellites: int = 10


class Settings(BaseSettings):
    db: DbConfig = DbConfig()
    predict: PredictConfig = PredictConfig()
    logging: LoggingConfig = LoggingConfig()
    hatchet: HatchetConfig = HatchetConfig()
    spacetrack: SpacetrackConfig = SpacetrackConfig()
    debug: bool = False
    orbit_insert_batch: int = 500

    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        nested_model_default_partial_update=True,
        extra="ignore",
        toml_file=["config.toml"],
        env_file=[".env"],
        secrets_dir="/run/secrets",
        validate_default=False,
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        return (
            init_settings,
            TomlConfigSettingsSource(settings_cls),
            file_secret_settings,
            dotenv_settings,
            env_settings,
        )


config = Settings()
