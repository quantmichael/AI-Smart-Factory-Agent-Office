"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager
from time import monotonic
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.errors import error_response
from app.api.exceptions import APIError
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.readiness import evaluate_readiness
from app.data.errors import DatasetNotFoundError, MeasurementNotFoundError
from app.ml.inference import (
    InferenceError,
    InvalidFeatureError,
    ModelLoadError,
    ModelNotFoundError,
)
from app.services.analysis import FeatureExtractionError

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):
    readiness = evaluate_readiness(settings)
    application.state.startup_readiness = readiness
    if readiness["status"] != "ready":
        logger.error("application dependencies are not ready", extra={"readiness": readiness})
        if settings.startup_validation_strict:
            raise RuntimeError("required application dependencies are not ready")
    else:
        logger.info("application dependencies are ready", extra={"readiness": readiness})
    yield

app = FastAPI(
    title="AI Smart Factory Agent Office API",
    version=settings.app_version,
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.middleware("http")
async def request_context_logging(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or f"req_{uuid4().hex}"
    request.state.request_id = request_id
    started = monotonic()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "API request completed",
        extra={
            "request_id": request_id,
            "run_id": request.path_params.get("run_id"),
            "endpoint": f"{request.method} {request.url.path}",
            "status": response.status_code,
            "latency_ms": (monotonic() - started) * 1000,
        },
    )
    return response


@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    logger.warning(
        "API request failed",
        extra={
            "request_id": getattr(request.state, "request_id", None),
            "run_id": request.path_params.get("run_id"),
            "endpoint": f"{request.method} {request.url.path}",
            "status": exc.status_code,
            "error_code": exc.code,
        },
    )
    return error_response(exc.status_code, exc.code, exc.message, exc.details)


@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return error_response(
        422,
        "INVALID_REQUEST",
        "Request validation failed.",
        {"errors": exc.errors()},
    )


@app.exception_handler(MeasurementNotFoundError)
async def measurement_not_found_handler(request: Request, exc: Exception) -> JSONResponse:
    return error_response(404, "MEASUREMENT_NOT_FOUND", "Measurement was not found.")


@app.exception_handler(ModelNotFoundError)
async def model_not_found_handler(request: Request, exc: Exception) -> JSONResponse:
    return error_response(404, "MODEL_NOT_FOUND", "Model was not found.")


@app.exception_handler(DatasetNotFoundError)
async def dataset_not_found_handler(request: Request, exc: Exception) -> JSONResponse:
    return error_response(500, "MEASUREMENT_NOT_FOUND", "Measurement dataset is unavailable.")


@app.exception_handler(ModelLoadError)
async def model_load_failed_handler(request: Request, exc: Exception) -> JSONResponse:
    return error_response(500, "MODEL_LOAD_FAILED", "Model could not be loaded.")


@app.exception_handler(InvalidFeatureError)
async def model_feature_mismatch_handler(request: Request, exc: Exception) -> JSONResponse:
    return error_response(500, "MODEL_FEATURE_MISMATCH", "Model feature contract is incompatible.")


@app.exception_handler(FeatureExtractionError)
async def feature_extraction_failed_handler(request: Request, exc: Exception) -> JSONResponse:
    return error_response(500, "FEATURE_EXTRACTION_FAILED", "Feature extraction failed.")


@app.exception_handler(InferenceError)
async def inference_failed_handler(request: Request, exc: Exception) -> JSONResponse:
    return error_response(500, "INFERENCE_FAILED", "Model inference failed.")
