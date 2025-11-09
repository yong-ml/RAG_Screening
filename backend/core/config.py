from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    # API Keys (.env에서 로드)
    gemini_api_key: str
    jina_api_key: str

    # Model Settings (기본값 설정, 환경변수로 오버라이드 가능)
    embedding_model: str = "BAAI/bge-m3"

    # Paths (기본값 설정, 환경변수로 오버라이드 가능)
    chroma_db_path: str = "./data/chroma_db"
    upload_dir: str = "./data/resumes"
    job_description_dir: str = "./data/jd"
    screening_results_dir: str = "./data/screening_results"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()
