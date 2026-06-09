"""Application configuration and settings management"""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    app_name: str = Field(default="User Service", alias="APP_NAME")
    debug: bool = Field(default=False)
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=5000)
    log_level: str = Field(default="INFO")
    
    # JWT Configuration
    jwt_secret_key: str = Field(default="your-super-secret-key-change-in-production")
    jwt_algorithm: str = Field(default="HS256")
    jwt_expire_minutes: int = Field(default=30)
    
    # Persistence Service
    persistence_service_url: str = Field(default="http://persistence-java.universidad.localhost:8080")
    request_timeout: int = Field(default=30)
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
