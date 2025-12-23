from pathlib import Path

from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str

    TOKEN: str

    @property
    def DB_URL(self) -> str:
        return (f"postgresql+asyncpg://"
                f"{self.DB_USER}:{self.DB_PASSWORD}@"
                f"{self.DB_HOST}:{self.DB_PORT}/"
                f"{self.DB_NAME}")

    class Config:
        env_file = str(ENV_FILE)
        case_sensitive = True


settings = Settings()
