from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Ramonyxs ERP Backend API"
    app_env: str = "development"
    debug: bool = False

    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/erp_db"

    jwt_secret_key: str = "change-this-secret-key"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_minutes: int = 60 * 24 * 7

    bootstrap_key: str = ""
    allow_registration: bool = False
    allow_bootstrap_when_users_exist: bool = False

    allowed_origins: str = "*"  # Change to string to avoid JSON parsing

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, value) -> str:
        # If it's already a list, convert back to string
        if isinstance(value, list):
            return ",".join(value)
        # If it's already a string, return as is
        if isinstance(value, str):
            return value
        # Fallback to empty string
        return "*"

    @property
    def allowed_origins_list(self) -> list[str]:
        """Get allowed origins as a list for CORS middleware."""
        if not self.allowed_origins or self.allowed_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    @property
    def is_development(self) -> bool:
        """Check if the application is running in development mode."""
        return self.app_env.lower() == "development"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
