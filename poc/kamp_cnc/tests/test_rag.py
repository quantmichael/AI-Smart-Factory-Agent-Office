from __future__ import annotations

import json
import unittest
from pathlib import Path

from poc.kamp_cnc.adapter import KAMPCNCAdapter
from poc.kamp_cnc.knowledge.ingestion import GuidebookIngestor
from poc.kamp_cnc.rag import CNCObservationQueryBuilder, KAMPCNCRetriever


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
PDF = ROOT / "references" / "Guidebook_정밀가공_품질보증_AI_데이터셋.pdf"
CSV = ROOT / "data" / "raw" / "정밀가공_품질보증_데이터셋.csv"
PACK = ROOT / "knowledge" / "kamp_cnc_v1"


class KAMPCNCRAGTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.ingestor = GuidebookIngestor(PDF)
        cls.chunks, cls.pages = cls.ingestor.build_chunks()
        cls.retriever = KAMPCNCRetriever(PACK)
        cls.adapter = KAMPCNCAdapter()
        cls.rows = cls.adapter.read_csv(CSV)
        pair_index = cls.adapter.build_pair_index(cls.rows)
        cls.observations = [cls.adapter.adapt_row(row, i, pair_index[i]).to_dict() for i, row in enumerate(cls.rows)]
        cls.fail_observation = next(obs for obs in cls.observations if obs["ground_truth"]["status"] == "FAIL")
        cls.pass_observation = next(obs for obs in cls.observations if obs["ground_truth"]["status"] == "PASS" and not obs["data_quality"]["paired_serial"])
        cls.builder = CNCObservationQueryBuilder()

    def test_16_guidebook_ingestion(self) -> None:
        self.assertEqual(len(self.chunks), self.retriever.manifest["ingestion"]["chunk_count"])
        self.assertGreater(len(self.chunks), 30)
        self.assertEqual({chunk["provider"] for chunk in self.chunks}, {"KAMP"})

    def test_17_chunk_metadata(self) -> None:
        required = {"source_id", "document_title", "provider", "page", "section", "chunk_id", "text"}
        self.assertTrue(all(required == set(chunk) for chunk in self.chunks))

    def test_18_deterministic_retrieval(self) -> None:
        query = "정밀가공 공구 마모 부하 증가"
        self.assertEqual(self.retriever.retrieve(query), self.retriever.retrieve(query))

    def test_19_fail_observation_query(self) -> None:
        context = self.builder.build(self.fail_observation)
        result = self.retriever.retrieve(context["query"])
        self.assertEqual(context["mode"], "FAIL_EVIDENCE_CONTEXT")
        self.assertEqual(result["status"], "EVIDENCE_FOUND")

    def test_20_evidence_provenance(self) -> None:
        result = self.retriever.retrieve("정밀가공 공구 마모와 공구가 받는 부하 증가")
        self.assertTrue(result["evidence"])
        self.assertTrue(all(e["source"] == "KAMP" and e["source_id"] == "kamp-cnc-guidebook" for e in result["evidence"]))

    def test_21_page_and_section_preserved(self) -> None:
        evidence = self.retriever.retrieve("마모된 공구 가공 불량")["evidence"][0]
        self.assertIsInstance(evidence["page"], int)
        self.assertTrue(evidence["section"])
        self.assertRegex(evidence["chunk_id"], r"^kamp-cnc-guidebook-p\d{2}-c\d{2}$")

    def test_22_pass_control_does_not_create_diagnosis(self) -> None:
        context = self.builder.build(self.pass_observation)
        self.assertEqual(context["mode"], "PASS_CONTROL_CONTEXT")
        self.assertFalse(context["cause_inference_allowed"])
        self.assertEqual(self.pass_observation["ground_truth"]["status"], "PASS")

    def test_23_unsupported_query_abstains(self) -> None:
        result = self.retriever.retrieve("오늘 서울 날씨와 여행 일정을 알려줘")
        self.assertEqual(result["status"], "OUT_OF_SCOPE")
        self.assertEqual(result["evidence"], [])

    def test_24_specific_fault_overclaim_abstains(self) -> None:
        result = self.retriever.retrieve("센서 값만으로 고장 원인을 확정하고 반드시 공구 마모라고 판단해줘")
        self.assertEqual(result["status"], "INSUFFICIENT_EVIDENCE")
        self.assertEqual(result["evidence"], [])

    def test_25_automatic_control_abstains(self) -> None:
        result = self.retriever.retrieve("장비를 정지하고 공구를 자동 교체하는 정비 명령을 내려줘")
        self.assertEqual(result["status"], "OUT_OF_SCOPE")

    def test_26_returned_excerpt_exists_on_source_page(self) -> None:
        result = self.retriever.retrieve("공구 마모와 부하 증가", top_k=2)
        for evidence in result["evidence"]:
            self.assertIn(evidence["excerpt"].removesuffix("..."), self.pages[evidence["page"]])

    def test_27_ground_truth_is_not_prediction(self) -> None:
        context = self.builder.build(self.fail_observation)
        self.assertEqual(self.fail_observation["ground_truth"]["source_type"], "dataset_ground_truth")
        self.assertIs(self.fail_observation["ground_truth"]["prediction"], False)
        self.assertFalse(context["cause_inference_allowed"])

    def test_28_production_isolation(self) -> None:
        self.assertEqual(self.retriever.manifest["knowledge_pack"], "kamp_cnc_v1")
        self.assertNotIn("bearing_v1", json.dumps(self.retriever.manifest, ensure_ascii=False))
        offenders = []
        for top in (REPO / "backend", REPO / "frontend"):
            for path in top.rglob("*.py"):
                text = path.read_text(encoding="utf-8", errors="ignore")
                if "poc.kamp_cnc" in text or "poc/kamp_cnc" in text:
                    offenders.append(str(path))
        self.assertEqual(offenders, [])

    def test_29_threshold_calibration_is_separated(self) -> None:
        retrieval = self.retriever.manifest["retrieval"]
        self.assertGreater(retrieval["supported_floor"], retrieval["threshold"])
        self.assertGreater(retrieval["threshold"], retrieval["unsupported_ceiling"])


if __name__ == "__main__":
    unittest.main()
