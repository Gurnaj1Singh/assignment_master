from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    SQLALCHEMY_DATABASE_URL: str

    # Email (OTP)
    MAIL_USERNAME: str = Field(..., validation_alias="MAIL_USERNAME")
    MAIL_PASSWORD: str = Field(..., validation_alias="MAIL_PASSWORD")
    MAIL_FROM: str = Field(..., validation_alias="MAIL_FROM")
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    USE_CREDENTIALS: bool = True

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # SBERT
    SBERT_MODEL_NAME: str = "all-mpnet-base-v2"
    SIMILARITY_THRESHOLD: float = 0.85

    # OpenAI (LLM question generation)
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
