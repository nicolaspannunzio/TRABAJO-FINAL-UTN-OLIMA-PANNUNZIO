from decimal import Decimal
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    supabase_url: str | None = None
    supabase_service_role_key: str | None = None
    supabase_jwt_secret: str | None = None
    cors_allowed_origin: str = "http://localhost:5173"
    umbral_variacion_default_pct: Decimal = Decimal("30.00")
    db_pool_min: int = 1
    db_pool_max: int = 5


@lru_cache
def get_settings() -> Settings:
    return Settings()