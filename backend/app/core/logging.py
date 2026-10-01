"""Application logging configuration."""

import logging


def configure_logging(level: str) -> None:
    """Configure concise, timestamped process-wide logging."""

    logging.basicConfig(
        level=level.upper(),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        force=True,
    )
