"""Common sensor dataset adapter contract."""

from abc import ABC, abstractmethod

from app.data.models import DatasetValidationResult, MeasurementSummary, StandardMeasurement


class SensorDatasetAdapter(ABC):
    """Minimal interface shared by supported sensor datasets."""

    @abstractmethod
    def list_measurements(self) -> tuple[MeasurementSummary, ...]:
        """Return metadata-only measurement records."""

    @abstractmethod
    def load_measurement(self, measurement_id: str) -> StandardMeasurement:
        """Load one indexed measurement and its raw signals."""

    @abstractmethod
    def get_metadata(self, measurement_id: str) -> MeasurementSummary:
        """Return metadata for one indexed measurement."""

    @abstractmethod
    def validate(self) -> DatasetValidationResult:
        """Validate every indexed measurement and return aggregate statistics."""
