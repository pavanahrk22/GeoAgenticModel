import functools
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./geoagentic.db"
    ROUTING_PROVIDER: str = "osrm"
    OSRM_BASE_URL: str = "https://router.project-osrm.org"
    ORS_BASE_URL: str = "https://api.openrouteservice.org"
    ORS_API_KEY: str = ""
    LLM_PROVIDER: str = "none"
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    CORS_ORIGINS: List[str] = ["http://localhost:5173"]
    SIMULATOR_TICK_INTERVAL: float = 1.0

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

@functools.lru_cache()
def get_settings() -> Settings:
    return Settings()
