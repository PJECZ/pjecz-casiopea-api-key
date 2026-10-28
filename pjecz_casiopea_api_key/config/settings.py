"""
Settings
"""

import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()
SERVICE_PREFIX = os.getenv("SERVICE_PREFIX", "pjecz_casiopea_api_key")


class Settings(BaseSettings):
    """Settings"""

    CONTROL_ACCESO_URL: str = os.getenv("CONTROL_ACCESO_URL", "")
    CONTROL_ACCESO_API_KEY: str = os.getenv("CONTROL_ACCESO_API_KEY", "")
    CONTROL_ACCESO_APLICACION: int = int(os.getenv("CONTROL_ACCESO_APLICACION", "0"))
    CONTROL_ACCESO_TIMEOUT: int = int(os.getenv("CONTROL_ACCESO_TIMEOUT", "0"))
    DB_HOST: str = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_NAME: str = os.getenv("DB_NAME", "pjecz_casiopea")
    DB_PASS: str = os.getenv("DB_PASS", "")
    DB_USER: str = os.getenv("DB_USER", "")
    FERNET_KEY: str = os.getenv("FERNET_KEY", "")
    ORIGINS: str = os.getenv("ORIGINS", "http://127.0.0.1:3000,http://localhost:3000")
    SENDGRID_API_KEY: str = os.getenv("SENDGRID_API_KEY", "")
    SENDGRID_FROM_EMAIL: str = os.getenv("SENDGRID_FROM_EMAIL", "")
    SALT: str = os.getenv("SALT", "")
    TZ: str = os.getenv("TZ", "America/Mexico_City")
    GOOGLE_APPLICATION_CREDENTIALS: str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    GCS_BUCKET_NAME: str = os.getenv("GCS_BUCKET_NAME", "")
    TURNOS_API_KEY: str = os.getenv("TURNOS_API_KEY", "")
    TURNOS_API_KEY_URL: str = os.getenv("TURNOS_API_KEY_URL", "")
    TURNOS_USUARIO_ID: int = int(os.getenv("TURNOS_USUARIO_ID", "0"))
    TURNOS_TIPO_ID: int = int(os.getenv("TURNOS_TIPO_ID", "0"))

    class Config:
        """Load configuration"""

        @classmethod
        def customise_sources(cls, init_settings, env_settings, file_secret_settings):
            """Customise sources, first environment variables, then .env file, then google cloud secret manager"""
            return env_settings, file_secret_settings, init_settings


@lru_cache()
def get_settings() -> Settings:
    """Get Settings"""
    return Settings()
