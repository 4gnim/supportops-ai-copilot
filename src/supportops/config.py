from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Application configuration loaded from environment variables and .env."""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "SupportOps AI Copilot"
    app_version: str = "0.1.0"
    api_key: str = Field(default="change-me-local-only", validation_alias="API_KEY")
    ollama_base_url: str = "http://localhost:11434"
    llm_model: str = "qwen3:4b-instruct"
    embedding_model: str = "intfloat/multilingual-e5-small"
    top_k: int = Field(default=4, ge=1, le=10)
    chunk_size: int = Field(default=700, ge=200, le=2000)
    chunk_overlap: int = Field(default=100, ge=0, le=500)
    collection_name: str = "supportops_knowledge"
    knowledge_dir: Path = PROJECT_ROOT / "data" / "knowledge"
    vector_store_dir: Path = PROJECT_ROOT / "storage" / "chroma"
    feedback_db_path: Path = PROJECT_ROOT / "storage" / "feedback.db"
    evaluation_dataset_path: Path = PROJECT_ROOT / "evaluation" / "golden_questions.jsonl"


settings = Settings()
