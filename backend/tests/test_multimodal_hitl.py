from app.agent.schemas import EvidenceStatus, HumanInputSubmission, VerificationResult
from agent_helpers import DeterministicEvidenceVerifier, build_fake_agent_service
from vision_helpers import build_vision_service, image_bytes


class ImageRequestThenSufficientVerifier:
    def __init__(self):
        self.calls = 0
        self.delegate = DeterministicEvidenceVerifier()

    def verify(self, candidates, evidence):
        self.calls += 1
        if self.calls == 1:
            return VerificationResult(
                status=EvidenceStatus.INSUFFICIENT,
                missing_information=["inspection image"],
                summary="A controlled exterior image request is required.",
            )
        return self.delegate.verify(candidates, evidence)


def test_hitl_image_upload_resumes_and_adds_visual_context(tmp_path):
    verifier = ImageRequestThenSufficientVerifier()
    service, _, _ = build_fake_agent_service(tmp_path / "checkpoint.sqlite3", verifier=verifier)
    vision = build_vision_service(tmp_path)
    service.dependencies.vision_service = vision
    waiting = service.start_run("fake:measurement:1", run_id="run-hitl-image")
    assert waiting["workflow_status"] == "WAITING"
    request = waiting["pending_human_request"]
    assert request["requested_fields"] == ["inspection_image_id"]
    image = vision.store(
        equipment_id="fake-rig", run_id="run-hitl-image", content=image_bytes(),
        mime_type="image/png", filename="operator-inspection.png",
    )
    completed = service.submit_human_input(
        "run-hitl-image",
        HumanInputSubmission(
            request_id=request["request_id"],
            response={"inspection_image_id": image.image_id},
            actor="test-operator",
        ),
    )
    assert completed["workflow_status"] == "COMPLETED"
    assert completed["visual_observations"][0]["image_id"] == image.image_id
    assert completed["diagnosis_candidates"][0]["supporting_visual_observation_ids"]
    service.close()
