from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
import os

_base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_root_dir = os.path.dirname(_base_dir)
_data_dir = os.path.join(_root_dir, "data")


class Settings(BaseSettings):
    # API Keys (.env에서 로드)
    gemini_api_key: str
    jina_api_key: str

    # Model Settings (기본값 설정, 환경변수로 오버라이드 가능)
    embedding_model: str = "BAAI/bge-m3"

    # Paths (기본값 설정, 환경변수로 오버라이드 가능)
    chroma_db_path: str = os.path.join(_data_dir, "chroma_db")
    upload_dir: str = os.path.join(_data_dir, "resumes")
    job_description_dir: str = os.path.join(_data_dir, "jd")
    screening_results_dir: str = os.path.join(_data_dir, "screening_results")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()
