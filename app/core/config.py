from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "HirePro AI"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # PostgreSQL
    POSTGRES_DB: str = "hirepro"
    POSTGRES_USER: str = "hirepro_user"
    POSTGRES_PASSWORD: str = "changeme"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    # JWT — secret must be overridden via .env in all real environments.
    # Generate a strong value with: openssl rand -hex 32
    JWT_SECRET_KEY: str = "CHANGE_ME_use_openssl_rand_hex_32"
    JWT_ALGORITHM: str = "HS256"
    # Access token lifetime in minutes (default 30 minutes).
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    @property
    def DATABASE_URL(self) -> str:
        """Async-compatible SQLAlchemy database URL."""
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
