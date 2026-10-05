"""Build retrieval context without turning Feature values into diagnoses."""

from __future__ import annotations

from typing import Any


class CNCObservationQueryBuilder:
    def build(self, observation: dict[str, Any]) -> dict[str, Any]:
        ground_truth = observation["ground_truth"]
        if ground_truth["prediction"] is not False or ground_truth["source_type"] != "dataset_ground_truth":
            raise ValueError("K2-1 requires non-predicted dataset ground truth")

        status = ground_truth["status"]
        features = observation["process_features"]
        context = {
            "SpindleSpeed_max": features["spindle_speed"]["max"],
            "SpindleLoad_max": features["spindle_load"]["max"],
            "SpindleLoad_std": features["spindle_load"]["std"],
            "ServoLoad_X_std": features["servo_load"]["X"]["std"],
            "ServoLoad_Z1_max": features["servo_load"]["Z1"]["max"],
        }
        if status == "FAIL":
            query = (
                "KAMP 정밀가공 제품 품질 Ground Truth 불량. "
                "Spindle Speed, Spindle Load, Servo Load 공정 데이터와 관련하여 "
                "Guidebook이 설명하는 공구 마모와 부하 증가, 가공 불량 가능성, "
                "작업자의 가공 설정값 및 공구 상태 점검 근거를 검색한다."
            )
            mode = "FAIL_EVIDENCE_CONTEXT"
        else:
            query = (
                "KAMP 정밀가공 제품 품질 Ground Truth 양품. "
                "Spindle Speed, Spindle Load, Servo Load 공정 데이터의 정의와 품질 관계 근거를 검색한다. "
                "제품 양품을 정상 설비 또는 고장 없음으로 확대 해석하지 않는다."
            )
            mode = "PASS_CONTROL_CONTEXT"
        return {
            "status": status,
            "mode": mode,
            "query": query,
            "feature_context": context,
            "cause_inference_allowed": False,
            "safety_note": "Feature values are retrieval context only and do not establish a specific fault cause.",
        }
