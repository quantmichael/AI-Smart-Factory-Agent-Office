"""Version 1 API router."""

from fastapi import APIRouter

from app.api.v1.analysis import router as analysis_router
from app.api.v1.agent import router as agent_router
from app.api.v1.health import router as health_router
from app.api.v1.knowledge import router as knowledge_router
from app.api.v1.models import router as models_router
from app.api.v1.system import router as system_router
from app.api.v1.equipment import router as equipment_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(analysis_router)
api_router.include_router(knowledge_router)
api_router.include_router(models_router)
api_router.include_router(system_router)
api_router.include_router(agent_router)
api_router.include_router(equipment_router)
