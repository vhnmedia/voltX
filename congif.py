"""
GreenWatt — Configuration
All secrets come from environment variables; never hardcode.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # ── App ─────────────────────────────────────────────────────────────────
    APP_NAME: str = "GreenWatt"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"   # development | staging | production

    # ── Supabase ─────────────────────────────────────────────────────────────
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str     # server-side; never expose to frontend
    DATABASE_URL: str                  # postgres://... (from Supabase → Settings → Database)

    # ── Redis / Celery ───────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── JWT ──────────────────────────────────────────────────────────────────
    JWT_SECRET: str = "change_me_in_production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_MINUTES: int = 60 * 8  # 8 hours

    # ── External APIs (simulated for hackathon) ──────────────────────────────
    IEX_API_BASE: str = "https://api.iexindia.com/v1"  # Official; use mock in dev
    IEX_API_KEY: Optional[str] = None
    WEATHER_API_BASE: str = "https://api.open-meteo.com/v1"

    # ── Mock Trading Partner API ─────────────────────────────────────────────
    # SIMULATION: This calls a mock endpoint. Replace with a CERC-registered
    # trading member's API URL in production after obtaining proper licensing.
    TRADING_PARTNER_API_BASE: str = "http://localhost:8001/mock-trading"
    TRADING_PARTNER_API_KEY: Optional[str] = "SIMULATED_KEY"
    USE_MOCK_TRADING_API: bool = True   # Flip to False only in production

    # ── ML Model Paths ───────────────────────────────────────────────────────
    MODEL_DIR: str = "./ml/models"
    PRICE_MODEL_VERSION: str = "latest"
    LOAD_MODEL_VERSION: str = "latest"

    # ── CO2 Estimation ───────────────────────────────────────────────────────
    # APPROXIMATION: grid emission factor, source: CEA 2023 annual report.
    # This is NOT a certified emissions figure.
    GRID_EMISSION_FACTOR_KG_PER_KWH: float = 0.716   # India average FY23

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
