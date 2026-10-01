"""Health API schemas."""

from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Liveness response returned by the API."""

    status: Literal["ok"]
    service: str
    version: str
