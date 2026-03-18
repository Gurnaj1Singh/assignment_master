from pydantic_settings import BaseSettings, SettingsConfigDict
from fastapi_mail import ConnectionConfig
from pydantic import Field
import os

class Settings(BaseSettings):
    # --- Database Settings ---
    DATABASE_URL: str 
    
    # --- Email Settings (For OTP) ---
    # Use Field with env_names to be extra safe
    MAIL_USERNAME: str = Field(..., validation_alias="MAIL_USERNAME")
    MAIL_PASSWORD: str = Field(..., validation_alias="MAIL_PASSWORD")
    MAIL_FROM: str = Field(..., validation_alias="MAIL_FROM")
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    USE_CREDENTIALS: bool = True
    SECRET_KEY: str 
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Updated: This tells Pydantic to look for .env in the current working directory
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding='utf-8',
        extra='ignore' # Ignores extra variables in .env
    )

# Initialize settings
settings = Settings()

# FastMail Configuration Object
conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=settings.USE_CREDENTIALS,
    VALIDATE_CERTS=True
)