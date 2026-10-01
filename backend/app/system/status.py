"""Side-effect-free, public-safe runtime status inspection."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from importlib.metadata import PackageNotFoundError, version as package_version
from pathlib import Path
import sqlite3
from typing import Callable

import joblib
from pydantic import Field

from app.core.config import Settings, resolve_runtime_path
from app.data.adapters.paderborn import PaderbornDatasetAdapter, SOURCE as DATASET_SOURCE
from app.domain.schemas.common import StrictSchema
from app.ml.registry import ArtifactModelRegistry
from app.rag.embedding import LocalHashingEmbeddingService
from app.rag.ingestion.manifest import load_manifest


class ComponentStatus(StrEnum):
    READY = "READY"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"
    UNKNOWN = "UNKNOWN"


class ComponentGroup(StrEnum):
    CORE_AI = "CORE_AI"
    KNOWLEDGE_AGENT = "KNOWLEDGE_AGENT"
    DATA_STATE = "DATA_STATE"
    VERSION_RUNTIME = "VERSION_RUNTIME"


class SystemDetail(StrictSchema):
    label: str
    value: str


class SystemComponent(StrictSchema):
    component_id: str
    name: str
    group: ComponentGroup
    status: ComponentStatus
    summary: str
    verification: str
    details: list[SystemDetail] = Field(default_factory=list)


class SystemStatusView(StrictSchema):
    overall_status: ComponentStatus
    checked_at: datetime
    application_version: str
    workflow_version: str
    components: list[SystemComponent]


def _detail(label: str, value: object) -> SystemDetail:
    return SystemDetail(label=label, value=str(value))


def _readonly_connection(path: Path) -> sqlite3.Connection:
    """Open an existing SQLite file without creating or mutating it."""

    if not path.is_file():
        raise FileNotFoundError(path.name)
    connection = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True, timeout=5)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only = ON")
    return connection


def _table_names(connection: sqlite3.Connection) -> set[str]:
    return {
        str(row[0])
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }


class SystemStatusService:
    """Inspect configured services without starting workflows or creating storage."""

    REQUIRED_COMPONENTS = {
        "backend_api",
        "ml_model",
        "dataset",
        "knowledge_base",
        "vector_db",
        "langgraph",
        "checkpoint_store",
        "run_database",
        "long_term_memory",
    }
    CRITICAL_COMPONENTS = {"backend_api", "ml_model"}

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def inspect(self) -> SystemStatusView:
        checks: list[Callable[[], SystemComponent]] = [
            self._backend,
            self._model,
            self._dataset,
            self._knowledge_base,
            self._vector_db,
            self._langgraph,
            self._checkpoint,
            self._run_database,
            self._memory,
            self._vision,
            self._runtime_versions,
        ]
        components: list[SystemComponent] = []
        for check in checks:
            try:
                components.append(check())
            except Exception:
                components.append(self._failed_component(check.__name__))
        return SystemStatusView(
            overall_status=self._overall_status(components),
            checked_at=datetime.now(UTC),
            application_version=self.settings.app_version,
            workflow_version=self.settings.workflow_version,
            components=components,
        )

    def _overall_status(self, components: list[SystemComponent]) -> ComponentStatus:
        indexed = {item.component_id: item for item in components}
        if any(
            indexed.get(component_id) is None
            or indexed[component_id].status is not ComponentStatus.READY
            for component_id in self.CRITICAL_COMPONENTS
        ):
            return ComponentStatus.UNAVAILABLE
        if any(
            indexed.get(component_id) is None
            or indexed[component_id].status is not ComponentStatus.READY
            for component_id in self.REQUIRED_COMPONENTS
        ):
            return ComponentStatus.DEGRADED
        return ComponentStatus.READY

    def _failed_component(self, check_name: str) -> SystemComponent:
        definitions = {
            "_backend": ("backend_api", "Backend API", ComponentGroup.CORE_AI),
            "_model": ("ml_model", "AI 모델", ComponentGroup.CORE_AI),
            "_dataset": ("dataset", "진단 데이터", ComponentGroup.CORE_AI),
            "_knowledge_base": ("knowledge_base", "Knowledge Base", ComponentGroup.KNOWLEDGE_AGENT),
            "_vector_db": ("vector_db", "Vector DB", ComponentGroup.KNOWLEDGE_AGENT),
            "_langgraph": ("langgraph", "LangGraph", ComponentGroup.KNOWLEDGE_AGENT),
            "_checkpoint": ("checkpoint_store", "Checkpoint Store", ComponentGroup.KNOWLEDGE_AGENT),
            "_run_database": ("run_database", "Run Database", ComponentGroup.DATA_STATE),
            "_memory": ("long_term_memory", "Long-term Memory", ComponentGroup.DATA_STATE),
            "_vision": ("multimodal", "Multimodal / Vision", ComponentGroup.DATA_STATE),
            "_runtime_versions": ("runtime_versions", "Version / Runtime", ComponentGroup.VERSION_RUNTIME),
        }
        component_id, name, group = definitions[check_name]
        return SystemComponent(
            component_id=component_id,
            name=name,
            group=group,
            status=ComponentStatus.UNAVAILABLE,
            summary="상태를 확인할 수 없습니다",
            verification="확인 과정에서 오류가 발생했으며 내부 오류 정보는 공개하지 않습니다.",
        )

    def _backend(self) -> SystemComponent:
        return SystemComponent(
            component_id="backend_api",
            name="Backend API",
            group=ComponentGroup.CORE_AI,
            status=ComponentStatus.READY,
            summary="상태 API 응답 가능",
            verification="현재 요청을 처리한 FastAPI 프로세스의 응답 여부를 확인했습니다.",
            details=[
                _detail("서비스", self.settings.app_name),
                _detail("App Version", self.settings.app_version),
            ],
        )

    def _model(self) -> SystemComponent:
        entry = ArtifactModelRegistry(
            resolve_runtime_path(self.settings.ml_artifact_root),
            self.settings.active_ml_model_id,
        ).get_active_model()
        bundle = joblib.load(entry.model_path)
        required = {"model", "model_id", "feature_names", "classes"}
        if not isinstance(bundle, dict) or not required.issubset(bundle):
            raise ValueError("invalid model contract")
        if str(bundle["model_id"]) != entry.model_id:
            raise ValueError("model identity mismatch")
        model = bundle["model"]
        return SystemComponent(
            component_id="ml_model",
            name="AI 모델",
            group=ComponentGroup.CORE_AI,
            status=ComponentStatus.READY,
            summary="모델 로드 가능",
            verification="실제 artifact를 역직렬화하고 필수 inference contract를 확인했습니다. 추론은 실행하지 않았습니다.",
            details=[
                _detail("Model ID", entry.model_id),
                _detail("Version", entry.metadata.get("version", "unknown")),
                _detail("Algorithm", type(model).__name__),
                _detail("Features", len(bundle["feature_names"])),
            ],
        )

    def _dataset(self) -> SystemComponent:
        adapter = PaderbornDatasetAdapter(
            resolve_runtime_path(self.settings.paderborn_data_root)
        )
        measurements = adapter.list_measurements()
        if not measurements:
            raise ValueError("empty dataset")
        return SystemComponent(
            component_id="dataset",
            name="진단 데이터",
            group=ComponentGroup.CORE_AI,
            status=ComponentStatus.READY,
            summary="Measurement 조회 가능",
            verification="Paderborn adapter가 실제 MAT 파일을 읽기 전용 인덱스로 구성했습니다. 전체 신호 로드는 실행하지 않았습니다.",
            details=[
                _detail("Dataset", "Paderborn Bearing DataCenter"),
                _detail("Measurements", len(measurements)),
                _detail("Source", DATASET_SOURCE),
            ],
        )

    def _manifest(self) -> tuple[dict, int]:
        knowledge_root = resolve_runtime_path(self.settings.knowledge_base_root)
        path = (
            knowledge_root
            / self.settings.knowledge_pack_id
            / "manifests"
            / "source_manifest.json"
        )
        payload, documents, _ = load_manifest(path, knowledge_root.parent)
        return payload, len(documents)

    def _knowledge_base(self) -> SystemComponent:
        payload, document_count = self._manifest()
        return SystemComponent(
            component_id="knowledge_base",
            name="Knowledge Base",
            group=ComponentGroup.KNOWLEDGE_AGENT,
            status=ComponentStatus.READY,
            summary="Manifest 조회 가능",
            verification="승인된 Source Manifest를 읽고 문서 목록을 검증했습니다. Vector 검색 가능 여부는 별도 카드에서 확인합니다.",
            details=[
                _detail("Knowledge Pack", self.settings.knowledge_pack_id),
                _detail("Version", payload.get("manifest_version", "unknown")),
                _detail("Documents", document_count),
            ],
        )

    def _vector_db(self) -> SystemComponent:
        path = resolve_runtime_path(self.settings.vector_db_path) / "chroma.sqlite3"
        with _readonly_connection(path) as connection:
            tables = _table_names(connection)
            required = {"collections", "segments", "embeddings", "embedding_metadata"}
            if not required.issubset(tables):
                raise ValueError("invalid vector database")
            collection = connection.execute(
                "SELECT id, name, dimension FROM collections WHERE name = ?",
                (self.settings.knowledge_pack_id,),
            ).fetchone()
            if collection is None:
                raise ValueError("collection unavailable")
            embedding_count = int(
                connection.execute(
                    """SELECT COUNT(*) FROM embeddings e
                       JOIN segments s ON s.id = e.segment_id
                       WHERE s.collection = ?""",
                    (collection["id"],),
                ).fetchone()[0]
            )
            document_count = int(
                connection.execute(
                    """SELECT COUNT(DISTINCT em.string_value)
                       FROM embedding_metadata em
                       JOIN embeddings e ON e.id = em.id
                       JOIN segments s ON s.id = e.segment_id
                       WHERE s.collection = ? AND em.key = 'document_id'""",
                    (collection["id"],),
                ).fetchone()[0]
            )
        embedding = LocalHashingEmbeddingService(self.settings.embedding_batch_size)
        return SystemComponent(
            component_id="vector_db",
            name="Vector DB",
            group=ComponentGroup.KNOWLEDGE_AGENT,
            status=ComponentStatus.READY,
            summary="Collection 조회 가능",
            verification="기존 Chroma SQLite를 read-only mode로 열어 collection과 embedding metadata를 조회했습니다.",
            details=[
                _detail("Engine", "Chroma"),
                _detail("Collection", collection["name"]),
                _detail("Documents", document_count),
                _detail("Embeddings", embedding_count),
                _detail("Embedding", embedding.config.model),
                _detail("Dimensions", collection["dimension"] or embedding.config.dimension),
                _detail("Distance", "cosine"),
            ],
        )

    def _langgraph(self) -> SystemComponent:
        try:
            library_version = package_version("langgraph")
        except PackageNotFoundError:
            raise RuntimeError("langgraph unavailable")
        return SystemComponent(
            component_id="langgraph",
            name="LangGraph",
            group=ComponentGroup.KNOWLEDGE_AGENT,
            status=ComponentStatus.READY,
            summary="Workflow 구성 확인",
            verification="LangGraph package와 구성 version을 확인했습니다. 이번 상태 조회에서 Workflow를 실행하지는 않았습니다.",
            details=[
                _detail("Workflow", self.settings.workflow_version),
                _detail("LangGraph", library_version),
                _detail("Runtime Check", "구성 확인 · 실행 안 함"),
            ],
        )

    def _checkpoint(self) -> SystemComponent:
        path = resolve_runtime_path(self.settings.agent_checkpoint_path)
        with _readonly_connection(path) as connection:
            if not {"checkpoints", "writes"}.issubset(_table_names(connection)):
                raise ValueError("invalid checkpoint store")
            threads, checkpoints = connection.execute(
                "SELECT COUNT(DISTINCT thread_id), COUNT(*) FROM checkpoints"
            ).fetchone()
        return SystemComponent(
            component_id="checkpoint_store",
            name="Checkpoint Store",
            group=ComponentGroup.KNOWLEDGE_AGENT,
            status=ComponentStatus.READY,
            summary="저장소 접근 가능",
            verification="기존 checkpoint SQLite를 read-only mode로 열고 필수 table을 조회했습니다.",
            details=[_detail("Run Threads", threads), _detail("Checkpoints", checkpoints)],
        )

    def _sqlite_count_component(
        self,
        *,
        component_id: str,
        name: str,
        path: Path,
        table: str,
        label: str,
    ) -> SystemComponent:
        with _readonly_connection(path) as connection:
            if table not in _table_names(connection):
                raise ValueError("required table unavailable")
            count = int(connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0])
        return SystemComponent(
            component_id=component_id,
            name=name,
            group=ComponentGroup.DATA_STATE,
            status=ComponentStatus.READY,
            summary="저장소 접근 가능",
            verification="기존 SQLite를 read-only mode로 열어 저장 건수를 조회했습니다.",
            details=[_detail(label, count)],
        )

    def _run_database(self) -> SystemComponent:
        return self._sqlite_count_component(
            component_id="run_database",
            name="Run Database",
            path=resolve_runtime_path(self.settings.agent_run_db_path),
            table="agent_runs",
            label="Stored Runs",
        )

    def _memory(self) -> SystemComponent:
        return self._sqlite_count_component(
            component_id="long_term_memory",
            name="Long-term Memory",
            path=resolve_runtime_path(self.settings.equipment_memory_db_path),
            table="equipment_memory",
            label="Records",
        )

    def _vision(self) -> SystemComponent:
        path = resolve_runtime_path(self.settings.inspection_image_db_path)
        with _readonly_connection(path) as connection:
            if not {"inspection_images", "visual_observations"}.issubset(
                _table_names(connection)
            ):
                raise ValueError("invalid vision database")
            images = int(connection.execute("SELECT COUNT(*) FROM inspection_images").fetchone()[0])
            observations = int(
                connection.execute("SELECT COUNT(*) FROM visual_observations").fetchone()[0]
            )
        enabled = self.settings.vision_enabled
        return SystemComponent(
            component_id="multimodal",
            name="Multimodal / Vision",
            group=ComponentGroup.DATA_STATE,
            status=ComponentStatus.READY if enabled else ComponentStatus.DEGRADED,
            summary="기능 사용 가능" if enabled else "기능 비활성화",
            verification="Vision 설정과 metadata DB 접근을 확인했습니다. 이미지 분석은 실행하지 않았습니다.",
            details=[
                _detail("Vision", "활성화" if enabled else "비활성화"),
                _detail("Model", self.settings.vision_model),
                _detail("Stored Images", images),
                _detail("Observations", observations),
            ],
        )

    def _runtime_versions(self) -> SystemComponent:
        return SystemComponent(
            component_id="runtime_versions",
            name="Version / Runtime",
            group=ComponentGroup.VERSION_RUNTIME,
            status=ComponentStatus.READY,
            summary="공개 가능한 버전 정보",
            verification="설정된 공개 version identifier만 표시하며 환경변수와 내부 경로는 제외했습니다.",
            details=[
                _detail("Application", self.settings.app_version),
                _detail("Workflow", self.settings.workflow_version),
                _detail("Model", self.settings.active_ml_model_id),
                _detail("Knowledge Pack", self.settings.knowledge_pack_id),
                _detail("Environment", self.settings.app_env),
            ],
        )
