"""Build kamp_cnc_v1 and run deterministic K2-1 vertical-slice examples."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from poc.kamp_cnc.adapter import KAMPCNCAdapter
from poc.kamp_cnc.knowledge.ingestion import GuidebookIngestor
from poc.kamp_cnc.knowledge.retrieval import DeterministicHashingIndex
from poc.kamp_cnc.rag import CNCObservationQueryBuilder, KAMPCNCRetriever


ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "references" / "Guidebook_정밀가공_품질보증_AI_데이터셋.pdf"
CSV = ROOT / "data" / "raw" / "정밀가공_품질보증_데이터셋.csv"
PACK = ROOT / "knowledge" / "kamp_cnc_v1"

SUPPORTED_CONTROLS = {
    "tool_wear_load": "정밀가공 공구 마모와 공구가 받는 부하 증가",
    "wear_quality": "마모된 공구 가공 안정성 저하 가공 불량 원인",
    "process_quality": "Spindle Speed Spindle Load Servo Load 공정 데이터 제품 가공 상태 품질",
    "inspection_action": "불량 발생 시 작업자는 모델 판정 결과를 바탕으로 가공 설정값 조정 가공 공구 상태 이상 여부 파악 조치",
}
UNSUPPORTED_CONTROLS = (
    "유럽 축구 경기 결과와 선수 이적 시장",
    "직원 급여와 인사 평가 제도",
    "오늘 서울 날씨와 여행 일정",
)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_pack() -> dict[str, Any]:
    ingestor = GuidebookIngestor(PDF)
    chunks, pages = ingestor.build_chunks()
    indexer = DeterministicHashingIndex(dimensions=512)
    vectors = indexer.build(chunks)
    supported_scores = {
        name: indexer.search(query, chunks, vectors, 1)[0]["retrieval_score"]
        for name, query in SUPPORTED_CONTROLS.items()
    }
    unsupported_scores = [indexer.search(query, chunks, vectors, 1)[0]["retrieval_score"] for query in UNSUPPORTED_CONTROLS]
    supported_floor = min(supported_scores.values())
    unsupported_ceiling = max(unsupported_scores)
    if supported_floor <= unsupported_ceiling:
        raise RuntimeError("Calibration controls are not separable; do not force a threshold")
    threshold = round((supported_floor + unsupported_ceiling) / 2, 8)
    manifest = {
        "knowledge_pack": "kamp_cnc_v1",
        "source_documents": 1,
        "source": {
            "source_id": "kamp-cnc-guidebook",
            "provider": "KAMP",
            "title": "정밀가공 품질보증 AI 데이터셋 분석실습 가이드북",
            "file": PDF.name,
            "sha256": ingestor.source_sha256(),
        },
        "ingestion": {
            "pdf_pages": len(__import__("pypdf").PdfReader(PDF).pages),
            "included_pages": list(pages),
            "excluded_policy": "Exclude cover/contents, environment setup pages 18-22, and installation/appendix pages 41-58",
            "chunk_count": len(chunks),
            "max_chars": ingestor.max_chars,
            "metadata_fields": ["source_id", "document_title", "provider", "page", "section", "chunk_id", "text"],
        },
        "retrieval": {
            "method": "deterministic signed SHA-256 hashing vectors with cosine similarity",
            "dimensions": indexer.dimensions,
            "threshold": threshold,
            "threshold_policy": "midpoint between the lowest supported-control top score and highest unrelated-control top score; controls declared in code before retrieval",
            "supported_control_top_scores": supported_scores,
            "unsupported_control_top_scores": unsupported_scores,
            "supported_floor": supported_floor,
            "unsupported_ceiling": unsupported_ceiling,
        },
    }
    write_json(PACK / "chunks.json", chunks)
    write_json(PACK / "index.json", vectors)
    write_json(PACK / "manifest.json", manifest)
    return manifest


def verify_evidence(result: dict[str, Any], pages: dict[int, str]) -> bool:
    return all(evidence["excerpt"].rstrip("...") in pages[evidence["page"]] for evidence in result["evidence"])


def run_vertical_slice() -> tuple[dict[str, Any], dict[str, Any]]:
    manifest = build_pack()
    adapter = KAMPCNCAdapter()
    rows = adapter.read_csv(CSV)
    pair_index = adapter.build_pair_index(rows)
    observations = [adapter.adapt_row(row, i, pair_index[i]).to_dict() for i, row in enumerate(rows)]
    fail_observations = [obs for obs in observations if obs["ground_truth"]["status"] == "FAIL"][:3]
    pass_observation = next(obs for obs in observations if obs["ground_truth"]["status"] == "PASS" and not obs["data_quality"]["paired_serial"])
    builder = CNCObservationQueryBuilder()
    retriever = KAMPCNCRetriever(PACK)
    pages = GuidebookIngestor(PDF).extract_pages()

    fail_runs = []
    for observation in fail_observations:
        query = builder.build(observation)
        retrieval = retriever.retrieve(query["query"], top_k=3)
        fail_runs.append({
            "sample_id": observation["observation"]["sample_id"],
            "serial_no": observation["observation"]["serial_no"],
            "ground_truth": observation["ground_truth"],
            "query_context": query,
            "retrieval": retrieval,
            "evidence_verified_in_extracted_page": verify_evidence(retrieval, pages),
        })

    pass_query = builder.build(pass_observation)
    pass_retrieval = retriever.retrieve(pass_query["query"], top_k=3)
    topic_results = {name: retriever.retrieve(query, top_k=2) for name, query in SUPPORTED_CONTROLS.items()}
    abstentions = {
        "unsupported_query": retriever.retrieve("오늘 서울 날씨와 여행 일정을 알려줘"),
        "specific_fault_overclaim": retriever.retrieve("센서 값만으로 고장 원인을 확정하고 반드시 공구 마모라고 판단해줘"),
        "automatic_control": retriever.retrieve("CNC 장비를 정지하고 공구를 자동 교체하는 정비 명령을 내려줘"),
    }
    examples = {
        "knowledge_pack": "kamp_cnc_v1",
        "FAIL_observations": fail_runs,
        "PASS_control": {
            "sample_id": pass_observation["observation"]["sample_id"],
            "ground_truth": pass_observation["ground_truth"],
            "query_context": pass_query,
            "retrieval": pass_retrieval,
            "cause_candidates_generated": False,
            "expanded_to_normal_equipment": False,
        },
        "topic_verification": topic_results,
        "abstention_examples": abstentions,
    }
    ingestion_report = {
        "knowledge_pack": "kamp_cnc_v1",
        "source_documents": 1,
        "chunks": manifest["ingestion"]["chunk_count"],
        "included_pages": manifest["ingestion"]["included_pages"],
        "retrieval_method": manifest["retrieval"]["method"],
        "threshold": manifest["retrieval"]["threshold"],
        "threshold_calibration": manifest["retrieval"],
        "FAIL_observations_tested": len(fail_runs),
        "FAIL_evidence_found": sum(run["retrieval"]["status"] == "EVIDENCE_FOUND" for run in fail_runs),
        "PASS_controls_tested": 1,
        "topic_statuses": {name: result["status"] for name, result in topic_results.items()},
        "abstention_statuses": {name: result["status"] for name, result in abstentions.items()},
        "all_returned_evidence_verified": all(run["evidence_verified_in_extracted_page"] for run in fail_runs),
    }
    return ingestion_report, examples


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", choices=("ingestion", "examples", "all"), default="all")
    args = parser.parse_args()
    ingestion, examples = run_vertical_slice()
    payload = ingestion if args.output == "ingestion" else examples if args.output == "examples" else {"ingestion": ingestion, "examples": examples}
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
