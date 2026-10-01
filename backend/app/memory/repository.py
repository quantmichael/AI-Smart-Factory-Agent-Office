"""SQLite repository dedicated to equipment memory (not RAG vectors)."""

from __future__ import annotations

from contextlib import contextmanager
import json
from pathlib import Path
import sqlite3

from app.memory.schemas import EquipmentMemoryRecord, MaintenanceRecord, MemoryType


class EquipmentMemoryRepository:
    def __init__(self, database_path: Path | str) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._setup()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        return connection

    @contextmanager
    def _connection(self):
        connection = self._connect()
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _setup(self) -> None:
        with self._connection() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS equipment_memory (
                    memory_id TEXT PRIMARY KEY,
                    equipment_id TEXT NOT NULL,
                    memory_type TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    record_json TEXT NOT NULL,
                    event_time TEXT NOT NULL,
                    recorded_at TEXT NOT NULL,
                    memory_version INTEGER NOT NULL,
                    UNIQUE (equipment_id, memory_type, source_type, source_id)
                );
                CREATE INDEX IF NOT EXISTS idx_equipment_memory_history
                    ON equipment_memory(equipment_id, event_time DESC);
                CREATE TABLE IF NOT EXISTS maintenance_records (
                    maintenance_id TEXT PRIMARY KEY,
                    equipment_id TEXT NOT NULL,
                    record_json TEXT NOT NULL,
                    performed_at TEXT NOT NULL,
                    recorded_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_maintenance_equipment_time
                    ON maintenance_records(equipment_id, performed_at DESC);
                """
            )

    def upsert(self, record: EquipmentMemoryRecord) -> EquipmentMemoryRecord:
        with self._connection() as connection:
            connection.execute(
                """INSERT INTO equipment_memory (
                       memory_id, equipment_id, memory_type, source_type, source_id,
                       status, summary, record_json, event_time, recorded_at, memory_version
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(equipment_id, memory_type, source_type, source_id)
                   DO UPDATE SET summary=excluded.summary, record_json=excluded.record_json,
                       status=excluded.status, event_time=excluded.event_time,
                       recorded_at=excluded.recorded_at, memory_version=excluded.memory_version""",
                (
                    record.memory_id, record.equipment_id, record.memory_type.value,
                    record.source_type.value, record.source_id, record.status.value,
                    record.summary, record.model_dump_json(), record.event_time.isoformat(),
                    record.recorded_at.isoformat(), record.memory_version,
                ),
            )
            row = connection.execute(
                """SELECT record_json FROM equipment_memory WHERE equipment_id=?
                   AND memory_type=? AND source_type=? AND source_id=?""",
                (record.equipment_id, record.memory_type.value, record.source_type.value, record.source_id),
            ).fetchone()
        return EquipmentMemoryRecord.model_validate_json(row["record_json"])

    def list_records(
        self, equipment_id: str, *, memory_types: set[MemoryType] | None = None, limit: int = 100
    ) -> list[EquipmentMemoryRecord]:
        query = "SELECT record_json FROM equipment_memory WHERE equipment_id = ?"
        params: list[object] = [equipment_id]
        if memory_types:
            placeholders = ",".join("?" for _ in memory_types)
            query += f" AND memory_type IN ({placeholders})"
            params.extend(item.value for item in sorted(memory_types, key=lambda item: item.value))
        query += " ORDER BY event_time DESC, recorded_at DESC LIMIT ?"
        params.append(limit)
        with self._connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [EquipmentMemoryRecord.model_validate_json(row["record_json"]) for row in rows]

    def count(self, equipment_id: str) -> int:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT COUNT(*) AS count FROM equipment_memory WHERE equipment_id=?",
                (equipment_id,),
            ).fetchone()
        return int(row["count"])

    def save_maintenance(self, record: MaintenanceRecord) -> MaintenanceRecord:
        with self._connection() as connection:
            connection.execute(
                """INSERT INTO maintenance_records
                   (maintenance_id, equipment_id, record_json, performed_at, recorded_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (record.maintenance_id, record.equipment_id, record.model_dump_json(),
                 record.performed_at.isoformat(), record.recorded_at.isoformat()),
            )
        return record

    def list_maintenance(self, equipment_id: str, *, limit: int = 50) -> list[MaintenanceRecord]:
        with self._connection() as connection:
            rows = connection.execute(
                """SELECT record_json FROM maintenance_records WHERE equipment_id=?
                   ORDER BY performed_at DESC LIMIT ?""",
                (equipment_id, limit),
            ).fetchall()
        return [MaintenanceRecord.model_validate_json(row["record_json"]) for row in rows]

    def delete_equipment(self, equipment_id: str) -> int:
        """Explicit retention control; callers decide authorization policy."""
        with self._connection() as connection:
            memories = connection.execute(
                "DELETE FROM equipment_memory WHERE equipment_id=?", (equipment_id,)
            ).rowcount
            maintenance = connection.execute(
                "DELETE FROM maintenance_records WHERE equipment_id=?", (equipment_id,)
            ).rowcount
        return memories + maintenance
