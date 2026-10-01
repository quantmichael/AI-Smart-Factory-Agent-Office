"""Stable public error payload helpers."""

from __future__ import annotations

from fastapi.responses import JSONResponse

from app.domain.schemas import ErrorDetail, ErrorResponse


def error_response(
    status_code: int,
    code: str,
    message: str,
    details: dict | None = None,
) -> JSONResponse:
    payload = ErrorResponse(
        error=ErrorDetail(code=code, message=message, details=details or {})
    )
    return JSONResponse(status_code=status_code, content=payload.model_dump(mode="json"))
