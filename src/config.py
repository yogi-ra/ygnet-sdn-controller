from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()


class Settings(BaseSettings):
    DATABASE_BASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./sdn_project.db")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")

    @property
    def DATABASE_URL(self) -> str:
        encoded_password = quote_plus(self.DB_PASSWORD)
        return self.DATABASE_BASE_URL.replace(
            "DB_PASSWORD_PLACEHOLDER", encoded_password
        )

    SECRET_KEY: str = os.getenv("SECRET_KEY", "your_super_secret_key_change_me")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
    NETMIKO_TIMEOUT: int = int(os.getenv("NETMIKO_TIMEOUT", 60))
    NETMIKO_READ_TIMEOUT: int = int(os.getenv("NETMIKO_READ_TIMEOUT", 60))
    MAX_WORKER_THREADS: int = int(os.getenv("MAX_WORKER_THREADS", 10)) # Added this line


settings = Settings()