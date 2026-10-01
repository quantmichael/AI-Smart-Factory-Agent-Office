"""Run the STEP 13 real-data multimodal and fallback validation scenarios."""

from __future__ import annotations

from datetime import UTC, datetime
from io import BytesIO
import json
from pathlib import Path
import sys
from uuid import uuid4

from PIL import Image, ImageDraw

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

from app.agent.factory import build_agent_service  # noqa: E402
from app.core.config import Settings  # noqa: E402


class ControlledFailureAnalyzer:
    provider_id = "validation"
    model_id = "controlled-timeout-v1"

    def analyze(self, image):
        raise TimeoutError("controlled STEP 13 fallback validation")


def resolved(path: Path) -> Path:
    return path if path.is_absolute() else (BACKEND_ROOT / path).resolve()


def demo_image() -> bytes:
    image = Image.new("RGB", (720, 480), (34, 42, 45))
    draw = ImageDraw.Draw(image)
    draw.rectangle((90, 110, 630, 390), fill=(85, 96, 98), outline=(185, 197, 198), width=6)
    draw.ellipse((230, 145, 490, 405), fill=(40, 48, 51), outline=(180, 190, 191), width=9)
    draw.ellipse((305, 220, 415, 330), fill=(16, 21, 23), outline=(120, 130, 132), width=5)
    draw.rectangle((470, 300, 590, 345), fill=(148, 91, 44))
    draw.text((96, 70), "SIMULATED INSPECTION INPUT - NOT PADERBORN GROUND TRUTH", fill=(239, 184, 91))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def dump(path: Path, payload) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n")


def main() -> None:
    settings = Settings()
    output = PROJECT_ROOT / "artifacts" / "multimodal"
    output.mkdir(parents=True, exist_ok=True)
    content = demo_image()
    (output / "simulated_inspection_input.png").write_bytes(content)
    workflow = build_agent_service(
        dataset_root=resolved(settings.paderborn_data_root),
        ml_artifact_root=resolved(settings.ml_artifact_root),
        active_model_id=settings.active_ml_model_id,
        vector_db_path=resolved(settings.vector_db_path),
        checkpoint_path=output / "runtime" / "checkpoints.sqlite3",
        memory_db_path=resolved(settings.equipment_memory_db_path),
        vision_db_path=output / "runtime" / "inspection_images.sqlite3",
        vision_upload_root=output / "runtime" / "uploads",
    )
    vision = workflow.dependencies.vision_service
    equipment_id = "paderborn-bearing-test-rig"
    measurement_id = "paderborn:KA01:N09_M07_F10:01"
    image = vision.store(
        equipment_id=equipment_id,
        content=content,
        mime_type="image/png",
        filename="simulated_inspection_input.png",
        description="Simulated workflow validation image; not synchronized Paderborn ground truth.",
    )
    run_id = f"run_multimodal_{uuid4().hex[:16]}"
    vision.attach(image.image_id, run_id, equipment_id)
    state = workflow.start_run(measurement_id, run_id=run_id, inspection_image_ids=[image.image_id])
    observation = vision.repository.get_observation(image.image_id)
    dump(output / "image_metadata_sample.json", image.model_dump(mode="json"))
    dump(output / "visual_observation_sample.json", observation.model_dump(mode="json"))
    dump(output / "multimodal_run.json", {
        "run_id": run_id,
        "measurement_id": measurement_id,
        "workflow_status": state["workflow_status"],
        "analysis_status": state["analysis_result"]["status"],
        "image_id": image.image_id,
        "visual_observations": state["visual_observations"],
        "rag_evidence_count": len(state["rag_evidence"]),
        "memory_context_count": len(state.get("memory_used_ids", [])),
        "diagnosis_candidates": state["diagnosis_candidates"],
        "dataset_relationship": "Separate simulated inspection input; not synchronized Paderborn ground truth.",
    })

    vision.analyzer = ControlledFailureAnalyzer()
    fallback_image = vision.store(
        equipment_id=equipment_id,
        content=content,
        mime_type="image/png",
        filename="simulated_fallback_input.png",
        description="Controlled vision-failure validation input.",
    )
    fallback_id = f"run_fallback_{uuid4().hex[:16]}"
    vision.attach(fallback_image.image_id, fallback_id, equipment_id)
    fallback = workflow.start_run(measurement_id, run_id=fallback_id, inspection_image_ids=[fallback_image.image_id])
    dump(output / "fallback_run.json", {
        "run_id": fallback_id,
        "workflow_status": fallback["workflow_status"],
        "vision_result": fallback["visual_observations"][0],
        "rag_evidence_count": len(fallback["rag_evidence"]),
        "final_report_available": bool(fallback.get("final_report")),
    })
    report = f"""# Multimodal Inspection Validation

- Generated at: {datetime.now(UTC).isoformat()}
- Run: `{run_id}`
- Measurement: `{measurement_id}`
- Inspection image: `{image.image_id}` (`simulated/demo`)
- Image quality: `{observation.quality.value}`
- Direct visual observations: {len(observation.observations)}
- Technical RAG evidence: {len(state['rag_evidence'])}
- Equipment memory context: {len(state.get('memory_used_ids', []))}
- Workflow status: `{state['workflow_status']}`
- Fallback run: `{fallback_id}` → `{fallback['workflow_status']}`
- Vision failure recorded as: `{fallback['visual_observations'][0]['analysis_error']}`

The image is a project-generated simulated inspection input. It is not an image
of the Paderborn test bearing and is not synchronized with the vibration sample.
The local observer reports only directly measurable image-quality properties and
does not infer an internal bearing fault. Sensor ML remains the primary current
measurement analysis, while visual observations, technical RAG evidence, and
equipment memory remain separate context sections.
"""
    (output / "MULTIMODAL_INSPECTION_REPORT.md").write_text(report)
    workflow.close()
    print(json.dumps({"run_id": run_id, "status": state["workflow_status"], "quality": observation.quality.value, "fallback_run_id": fallback_id, "fallback_status": fallback["workflow_status"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
