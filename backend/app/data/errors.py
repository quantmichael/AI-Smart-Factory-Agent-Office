"""Data adapter error types."""


class DatasetError(RuntimeError):
    """Base error for dataset discovery and loading."""


class DatasetNotFoundError(DatasetError):
    """Raised when the configured dataset root does not exist."""


class MeasurementNotFoundError(DatasetError):
    """Raised when a measurement ID is not in the adapter's internal index."""


class UnsupportedMatFormatError(DatasetError):
    """Raised when a MAT file is not a supported classic MATLAB file."""


class InvalidMeasurementError(DatasetError):
    """Raised when an indexed source does not match the observed dataset structure."""
