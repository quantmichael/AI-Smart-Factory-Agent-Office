"""Environment-backed application configuration."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_ROOT = Path(__file__).resolve().parents[2]


def resolve_runtime_path(path: Path | str) -> Path:
    """Resolve configured relative paths from backend/, independent of process cwd."""

    candidate = Path(path).expanduser()
    return candidate if candidate.is_absolute() else (BACKEND_ROOT / candidate).resolve()


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables or a local .env file."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    app_name: str = "ai-smart-factory-agent-office-api"
    app_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    openai_api_key: str | None = Field(default=None, repr=False)

    paderborn_data_root: Path = Path("../data/paderborn")
    knowledge_base_root: Path = Path("../knowledge")
    model_root: Path = Path("../models")
    ml_artifact_root: Path = Path("../artifacts/ml")
    active_ml_model_id: str = "bearing_rf_binary_v1"
    database_url: str = "sqlite:///./app.db"
    vector_db_path: Path = Path("../artifacts/vector_db")
    embedding_provider: str = "local"
    embedding_model: str = "sklearn-hashing-vectorizer-v1"
    embedding_batch_size: int = Field(default=64, ge=1, le=512)
    agent_checkpoint_path: Path = Path("../artifacts/agent/checkpoints/langgraph_core.sqlite3")
    agent_run_db_path: Path = Path("../artifacts/api/runtime/agent_runs.sqlite3")
    equipment_memory_db_path: Path = Path("../artifacts/memory/equipment_memory.sqlite3")
    inspection_image_db_path: Path = Path("../artifacts/multimodal/inspection_images.sqlite3")
    inspection_upload_root: Path = Path("../artifacts/multimodal/uploads")
    vision_enabled: bool = True
    vision_model: str = "pillow-quality-observer-v1"
    max_image_size_mb: int = Field(default=8, ge=1, le=50)
    max_image_dimension: int = Field(default=4096, ge=256, le=16384)
    agent_background_workers: int = Field(default=4, ge=1, le=16)
    sse_poll_interval_seconds: float = Field(default=0.1, ge=0.01, le=5.0)
    sse_heartbeat_seconds: float = Field(default=15.0, ge=1.0, le=60.0)
    max_retrieval_retries: int = Field(default=2, ge=0, le=5)
    max_human_information_rounds: int = Field(default=2, ge=0, le=5)
    max_action_revision_rounds: int = Field(default=1, ge=0, le=3)
    knowledge_pack_id: str = "bearing_v1"
    workflow_version: str = "diagnosis_core_v1"
    startup_validation_strict: bool = False

    @property
    def cors_origin_list(self) -> list[str]:
        """Return configured origins as a normalized list."""

        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return one settings instance per process."""

    return Settings()
