from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Laravel Backend
    laravel_api_url: str
    laravel_api_token: str
    
    # LLM API Keys
    anthropic_api_key: str
    openai_api_key: str | None = None
    
    # Model Configuration
    primary_model: str = "claude-3-5-sonnet-20241022"
    fallback_model: str | None = "gpt-4o"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
