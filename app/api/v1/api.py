from fastapi import APIRouter
from app.api.v1.endpoints import docs

api_router = APIRouter()

# Incluir los endpoints de documentación
api_router.include_router(docs.router, prefix="/docs", tags=["documents"]) 