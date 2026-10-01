"""SQLite metadata repository; image binaries remain in file storage."""

from contextlib import contextmanager
import json
from pathlib import Path
import sqlite3

from app.vision.schemas import InspectionImageRecord, VisualObservation


class InspectionImageRepository:
    def __init__(self, database_path: Path | str) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._setup()

    @contextmanager
    def _connection(self):
        connection = sqlite3.connect(self.database_path, timeout=30)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def _setup(self) -> None:
        with self._connection() as connection:
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS inspection_images (
                    image_id TEXT PRIMARY KEY, run_id TEXT, equipment_id TEXT NOT NULL,
                    record_json TEXT NOT NULL, uploaded_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_inspection_images_run ON inspection_images(run_id);
                CREATE TABLE IF NOT EXISTS visual_observations (
                    image_id TEXT PRIMARY KEY, result_json TEXT NOT NULL, created_at TEXT NOT NULL,
                    FOREIGN KEY(image_id) REFERENCES inspection_images(image_id)
                );
            """)

    def save_image(self, record: InspectionImageRecord) -> InspectionImageRecord:
        with self._connection() as connection:
            connection.execute(
                "INSERT INTO inspection_images VALUES (?, ?, ?, ?, ?)",
                (record.image_id, record.run_id, record.equipment_id, record.model_dump_json(), record.uploaded_at.isoformat()),
            )
        return record

    def get_image(self, image_id: str) -> InspectionImageRecord | None:
        with self._connection() as connection:
            row = connection.execute("SELECT record_json FROM inspection_images WHERE image_id = ?", (image_id,)).fetchone()
        return InspectionImageRecord.model_validate_json(row["record_json"]) if row else None

    def attach(self, image_id: str, run_id: str, equipment_id: str) -> InspectionImageRecord:
        record = self.get_image(image_id)
        if record is None:
            raise KeyError(image_id)
        if record.equipment_id != equipment_id:
            raise ValueError("inspection image belongs to a different equipment")
        if record.run_id not in (None, run_id):
            raise ValueError("inspection image is already attached to another run")
        attached = record.model_copy(update={"run_id": run_id})
        with self._connection() as connection:
            connection.execute(
                "UPDATE inspection_images SET run_id = ?, record_json = ? WHERE image_id = ?",
                (run_id, attached.model_dump_json(), image_id),
            )
        return attached

    def list_for_run(self, run_id: str) -> list[InspectionImageRecord]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT record_json FROM inspection_images WHERE run_id = ? ORDER BY uploaded_at", (run_id,)
            ).fetchall()
        return [InspectionImageRecord.model_validate_json(row["record_json"]) for row in rows]

    def save_observation(self, result: VisualObservation) -> VisualObservation:
        with self._connection() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO visual_observations VALUES (?, ?, ?)",
                (result.image_id, result.model_dump_json(), result.created_at.isoformat()),
            )
        return result

    def get_observation(self, image_id: str) -> VisualObservation | None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT result_json FROM visual_observations WHERE image_id = ?", (image_id,)
            ).fetchone()
        return VisualObservation.model_validate_json(row["result_json"]) if row else None
