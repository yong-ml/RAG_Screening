from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    # API Keys
    gemini_api_key: str
    jina_api_key: str

    # Model Settings
    embedding_model: str = "BAAI/bge-m3"

    # Database
    chroma_db_path: str = "./data/chroma_db"

    # Upload
    upload_dir: str = "./data/resumes"

    model_config = SettingsConfigDict(env_file=".env")


@lru_cache()
def get_settings() -> Settings:
    return Settings()
