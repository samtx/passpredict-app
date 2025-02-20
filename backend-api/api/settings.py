from pathlib import Path
from typing import Literal

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv


load_dotenv(Path(__file__).parent.parent.joinpath(".env"))


class HatchetConfig(BaseModel):
    token: str = None
    tenant_id: str = None
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
    model_config = SettingsConfigDict(
        env_prefix="PPAPI_",
        env_nested_delimiter="__",
        extra="ignore",
    )
    db_url: str = "sqlite+aiosqlite:///./ppapi.db"
    predict: PredictConfig = PredictConfig()
    logging: LoggingConfig = LoggingConfig()
    hatchet: HatchetConfig = HatchetConfig()
    debug: bool = False


config = Settings()
