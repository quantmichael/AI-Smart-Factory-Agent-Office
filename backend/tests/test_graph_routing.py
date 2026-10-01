from app.agent.routing import route_analysis, route_evidence


def test_normal_and_abnormal_routing_is_deterministic() -> None:
    assert route_analysis({"analysis_result": {"status": "normal"}}) == "normal"
    assert route_analysis({"analysis_result": {"status": "abnormal"}}) == "abnormal"


def test_all_evidence_status_routes() -> None:
    base = {"retrieval_retry_count": 0, "max_retrieval_retries": 2}
    assert route_evidence({**base, "evidence_status": "SUFFICIENT"}) == "sufficient"
    assert route_evidence({**base, "evidence_status": "PARTIAL"}) == "refine"
    assert route_evidence({**base, "evidence_status": "INSUFFICIENT"}) == "additional_information"
    assert route_evidence({**base, "evidence_status": "CONFLICTING"}) == "counter_evidence"
