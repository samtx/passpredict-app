import os
from pathlib import Path
from typing import Literal
from collections.abc import Sequence

from pydantic import BaseModel, SecretStr, Field
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
    TomlConfigSettingsSource,
    EnvSettingsSource,
    DotEnvSettingsSource,
)


API_ROOT_DIR = Path(__file__).parent


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


class PaginateConfig(BaseModel):
    max_limit: int = 100


class Settings(BaseSettings):
    db: DbConfig = DbConfig()
    predict: PredictConfig = PredictConfig()
    logging: LoggingConfig = LoggingConfig()
    hatchet: HatchetConfig = HatchetConfig()
    spacetrack: SpacetrackConfig = SpacetrackConfig()
    paginate: PaginateConfig = PaginateConfig()
    debug: bool = False
    orbit_insert_batch: int = 500
    static_dir: Path = API_ROOT_DIR.joinpath("static")
    template_dir: Path = API_ROOT_DIR.joinpath("templates")

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
            env_settings,
            TomlConfigSettingsSource(settings_cls),
            dotenv_settings,
            DotEnvDirSettingsSource(settings_cls, API_ROOT_DIR.parent.joinpath('.secrets')),
            file_secret_settings,
        )


PathType = Path | str | Sequence[Path | str]


class DotEnvDirSettingsSource(DotEnvSettingsSource):

    def __init__(
        self,
        settings_cls: type[BaseSettings],
        env_file_dir: PathType,
        env_file_encoding: str | None = None,
        case_sensitive: bool | None = None,
        env_prefix: str | None = None,
        env_nested_delimiter: str | None = None,
        env_nested_max_split: int | None = None,
        env_ignore_empty: bool | None = None,
        env_parse_none_str: str | None = None,
        env_parse_enums: bool | None = None,
    ) -> None:
        env_file_dirs = [env_file_dir] if isinstance(env_file_dir, (str, os.PathLike)) else env_file_dir
        env_dir_paths = [Path(p).expanduser() for p in env_file_dirs]
        env_files = []
        for dir_path in env_dir_paths:
            for f in dir_path.iterdir():
                env_files.append(f)

        super().__init__(
            settings_cls,
            env_files,
            env_file_encoding=env_file_encoding,
            case_sensitive=case_sensitive,
            env_prefix=env_prefix,
            env_nested_delimiter=env_nested_delimiter,
            env_nested_max_split=env_nested_max_split,
            env_ignore_empty=env_ignore_empty,
            env_parse_none_str=env_parse_none_str,
            env_parse_enums=env_parse_enums,
        )




config = Settings()
