"""Validate the canonical source manifest and expand document collections."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Iterable

from app.rag.models import IngestionStatus, KnowledgeDocument
from app.data.adapters.paderborn import GROUND_TRUTH


DOCUMENT_TYPE_BY_SOURCE = {
    "PADERBORN_OVERVIEW": "dataset_overview",
    "PADERBORN_DATASETS_AND_DOWNLOAD": "dataset_overview",
    "PADERBORN_DAMAGE": "damage_fact_sheet",
    "PADERBORN_TEST_RIG": "experiment_description",
    "PADERBORN_OPERATING_CONDITIONS": "experiment_description",
    "PADERBORN_PUBLICATION": "publication",
    "PADERBORN_BENCHMARK_PAPER": "publication",
    "SKF_VIBRATION_DIAGNOSTIC_GUIDE": "vibration_diagnostic_guide",
    "SKF_BEARING_DAMAGE_FAILURE_ANALYSIS": "failure_analysis_guide",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def collection_sha256(paths: Iterable[Path], project_root: Path | None = None) -> str | None:
    paths = sorted(paths)
    if not paths:
        return None
    digest = hashlib.sha256()
    for path in paths:
        identity = path.relative_to(project_root) if project_root else path
        digest.update(str(identity).encode("utf-8"))
        digest.update(b"\0")
        digest.update(sha256_file(path).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def _document_id(source_id: str, suffix: str | None = None) -> str:
    value = source_id.lower()
    if suffix:
        value += "_" + suffix.lower()
    return re.sub(r"[^a-z0-9_]+", "_", value).strip("_")


def _safe_path(project_root: Path, local_path: str) -> Path:
    candidate = (project_root / local_path).resolve()
    try:
        candidate.relative_to(project_root.resolve())
    except ValueError as exc:
        raise ValueError(f"manifest path escapes project root: {local_path}") from exc
    return candidate


def _base_document(record: dict, path: Path, *, suffix: str | None, document_type: str) -> KnowledgeDocument:
    bearing_id = suffix.upper() if suffix else None
    title = record["title"] if not suffix else f"{record['title']} — {bearing_id}"
    metadata = {"bearing_id": bearing_id} if bearing_id else {}
    if document_type == "damage_fact_sheet" and bearing_id in GROUND_TRUTH:
        truth = GROUND_TRUTH[bearing_id]
        metadata.update(
            {
                "bearing_state": truth.state,
                "fault_type": truth.fault_type,
                "damage_location": truth.damage_location,
                "damage_mechanism": truth.damage_mechanism,
                "ground_truth_evidence_reference": truth.evidence_reference,
            }
        )
    return KnowledgeDocument(
        document_id=_document_id(record["source_id"], suffix),
        source_id=record["source_id"],
        knowledge_pack_id="bearing_v1",
        title=title,
        publisher=record["publisher"],
        document_type=document_type,
        source_tier=int(str(record["source_tier"]).split()[-1]),
        rag_roles=list(record["rag_role"]),
        official_url=record["official_url"],
        local_path=path.as_posix(),
        sha256=sha256_file(path),
        version="1",
        license=record.get("license", ""),
        license_status=record.get("license_status", ""),
        ingestion_status=IngestionStatus.READY,
        metadata=metadata,
    )


def load_manifest(manifest_path: Path | str, project_root: Path | str) -> tuple[dict, list[KnowledgeDocument], list[dict]]:
    manifest_path = Path(manifest_path)
    project_root = Path(project_root).resolve()
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not payload.get("manifest_version") or not isinstance(payload.get("sources"), list):
        raise ValueError("invalid source manifest structure")
    documents: list[KnowledgeDocument] = []
    source_statuses: list[dict] = []
    required = {
        "source_id", "title", "publisher", "official_url", "local_path",
        "source_tier", "rag_role", "license_status", "sha256", "file_type",
    }
    for record in payload["sources"]:
        missing = required.difference(record)
        if missing:
            raise ValueError(f"manifest source missing fields: {sorted(missing)}")
        path = _safe_path(project_root, record["local_path"])
        file_type = record["file_type"]
        status = IngestionStatus.READY
        expanded: list[KnowledgeDocument] = []
        warning = None
        if file_type == "rar_collection":
            status = IngestionStatus.UNSUPPORTED
            warning = "Dataset archives are not textual RAG documents."
        elif file_type == "pdf_collection":
            if record["source_id"] == "PADERBORN_DAMAGE_FACT_SHEETS":
                paths = [p for p in path.glob("*/*.pdf") if not p.name.startswith("measuring_log_")]
                doc_type = "damage_fact_sheet"
            else:
                paths = list(path.glob("*/measuring_log_*.pdf"))
                doc_type = "measurement_log"
            digest = collection_sha256(paths, project_root)
            if not paths:
                status = IngestionStatus.MISSING
            elif digest != record["sha256"]:
                status = IngestionStatus.INVALID
                warning = "Collection SHA-256 does not match the manifest."
            else:
                for item in sorted(paths):
                    expanded.append(
                        _base_document(record, item, suffix=item.parent.name, document_type=doc_type)
                    )
        elif file_type in {"pdf", "html"}:
            if not path.is_file():
                status = IngestionStatus.MISSING
            elif sha256_file(path) != record["sha256"]:
                status = IngestionStatus.INVALID
                warning = "SHA-256 does not match the manifest."
            else:
                expanded.append(
                    _base_document(
                        record,
                        path,
                        suffix=None,
                        document_type=DOCUMENT_TYPE_BY_SOURCE.get(record["source_id"], "other"),
                    )
                )
        else:
            status = IngestionStatus.UNSUPPORTED
            warning = f"Unsupported manifest file type: {file_type}"
        documents.extend(expanded)
        source_statuses.append(
            {
                "source_id": record["source_id"],
                "status": status.value,
                "document_count": len(expanded),
                "warning": warning,
            }
        )
    ids = [document.document_id for document in documents]
    if len(ids) != len(set(ids)):
        raise ValueError("expanded document IDs are not unique")
    return payload, documents, source_statuses
