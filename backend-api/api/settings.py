import os
from pathlib import Path
from typing import Literal, Any, Annotated
from collections.abc import Sequence
import warnings
from base64 import b64decode

from pydantic import (
    BaseModel,
    SecretStr,
    Field,
    computed_field,
    model_validator,
    AfterValidator,
    BeforeValidator,
    PlainSerializer,
)
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
    TomlConfigSettingsSource,
    EnvSettingsSource,
    DotEnvSettingsSource,
)
from hatchet_sdk import RateLimitDuration


def SetEnvVar(env_var: str):
    def set_env_var(value: Any) -> Any:
        os.environ[env_var] = value
        return value
    return AfterValidator(set_env_var)


API_ROOT_DIR = Path(__file__).parent


def map_string_to_enum(value: Any) -> RateLimitDuration:
    if isinstance(value, RateLimitDuration):
        return value
    match str(value).capitalize():
        case "SECOND":
            return RateLimitDuration.SECOND
        case "MINUTE":
            return RateLimitDuration.MINUTE
        case "HOUR":
            return RateLimitDuration.HOUR
        case "WEEK":
            return RateLimitDuration.WEEK
        case "MONTH":
            return RateLimitDuration.MONTH
        case "YEAR":
            return RateLimitDuration.YEAR
        case _:
            raise ValueError(f"{value} not among possible options.")


def serialize_enum_to_str(value: RateLimitDuration) -> str:
    return RateLimitDuration.Name(value)


class DbConfig(BaseModel):
    scheme: str = "sqlite+aiosqlite"
    path: Path = API_ROOT_DIR.joinpath("ppapi.db")
    echo: bool = False

    @computed_field
    @property
    def file_uri(self) -> str:
        return f"file:{str(self.path.resolve())}"

    def sqlalchemy_conn_url(
        self,
        sync: bool = False,
        read_only: bool = False,
    ) -> str:
        url = f"{self.scheme}:///{self.file_uri}?uri=true"
        if read_only:
            url = url + "&mode=ro"
        if sync:
            url = url.replace("+aiosqlite", "")
        return url


class FetchConfig(BaseModel):
    key: str
    cron: str
    limit: int
    duration: Literal["SECOND", "MINUTE", "HOUR", "DAY", "WEEK", "MONTH", "YEAR"]


class SpacetrackConfig(BaseModel):
    username: str = ""
    password: SecretStr = ""
    auth: str = ""
    auth_file: Path | None = None
    auth_file_encoding: str = "utf-8"
    base_url: str = "https://www.space-track.org"
    auth_endpoint: str = "/ajaxauth/login"
    http_timeout: float = 30
    gp_fetch: FetchConfig = FetchConfig(
        key="spacetrack-gp-request",
        cron="17 4,12,20 * * *",
        limit=1,
        duration="HOUR",
    )
    gp_epoch_days_since: float = 3
    satcat_fetch: FetchConfig = FetchConfig(
        key="spacetrack-satcat-request",
        cron="44 11 * * *",
        limit=1,
        duration="DAY",
    )

    @model_validator(mode="after")
    def get_credentials_from_files(self) -> 'SpacetrackConfig':

        def b64_decode_auth(auth: str) -> tuple[str, SecretStr]:
            username, password = b64decode(auth).decode().split(":")
            return (username, SecretStr(password))

        def read_from_file(attr: str) -> str:
            file_path = getattr(self, attr)
            encoding = getattr(self, f"{attr}_encoding", "utf-8")
            with open(file_path, "rt", encoding=encoding) as f:
                return f.read()

        if self.auth_file is not None:
            auth = read_from_file('auth_file')
            self.username, self.password = b64_decode_auth(auth)
        elif self.auth:
            self.username, self.password = b64_decode_auth(self.auth)

        return self


class HatchetConfig(BaseModel):
    token: SecretStr = ""
    token_file: Path | None = None
    token_file_encoding: str = "utf-8"
    # tenant_id: str = ""
    tls: Annotated[Literal["none", "tls", "mtls"], Field(validate_default=True), SetEnvVar("HATCHET_CLIENT_TLS_STRATEGY")] = "none"
    namespace: str = ""
    debug: bool = False
    # grpc_host: Annotated[str, Field(validate_default=True), SetEnvVar("HATCHET_CLIENT_HOST_PORT")] = "localhost:7077"
    # server_url: str = "localhost:8888"

    @model_validator(mode="after")
    def get_token_from_file(self) -> 'HatchetConfig':
        if self.token_file is not None:
            with open(self.token_file, "rt", encoding=self.token_file_encoding) as f:
                self.token = SecretStr(f.read())
        return self



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
            DotEnvDirSettingsSource(settings_cls, "/run/secrets"),
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
        env_ignore_empty: bool | None = None,
        env_parse_none_str: str | None = None,
        env_parse_enums: bool | None = None,
    ) -> None:
        env_file_dirs = [env_file_dir] if isinstance(env_file_dir, (str, os.PathLike)) else env_file_dir
        env_dir_paths = [Path(p).expanduser() for p in env_file_dirs]
        env_files = []
        for dir_path in env_dir_paths:
            if not dir_path.exists():
                warnings.warn(f'directory "{dir_path}" does not exist')
                continue
            for f in dir_path.iterdir():
                if f.suffix == '.env':
                    env_files.append(f)

        super().__init__(
            settings_cls,
            env_files,
            env_file_encoding=env_file_encoding,
            case_sensitive=case_sensitive,
            env_prefix=env_prefix,
            env_nested_delimiter=env_nested_delimiter,
            env_ignore_empty=env_ignore_empty,
            env_parse_none_str=env_parse_none_str,
            env_parse_enums=env_parse_enums,
        )




config = Settings()
