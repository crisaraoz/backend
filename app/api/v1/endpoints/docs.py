from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl
from typing import List, Dict, Any, Optional
import asyncio
import time
from app.services.docs import (
    process_documentation,
    get_documentation_status,
    query_documentation
)

router = APIRouter()

class DocumentUrlInput(BaseModel):
    url: HttpUrl
    language_code: str = "es"
    analyze_subsections: bool = True
    max_depth: int = 3
    excluded_paths: List[str] = []

class DocumentStatusResponse(BaseModel):
    url: str
    status: str
    sections_analyzed: int
    total_pages: int
    completion_percentage: float
    message: str

class DocumentQueryInput(BaseModel):
    url: HttpUrl
    query: str
    language_code: str = "es"
    include_sources: bool = True

class DocumentQueryResponse(BaseModel):
    answer: str
    sources: List[str] = []
    confidence: float

# Diccionario para almacenar las tareas en segundo plano
background_tasks = {}

@router.post("/scrape", response_model=DocumentStatusResponse)
async def start_documentation_processing(data: DocumentUrlInput, background_tasks_manager: BackgroundTasks):
    """
    Inicia el procesamiento de documentación en segundo plano.
    Retorna de inmediato con el estado inicial.
    """
    try:
        url = str(data.url)
        
        # Iniciar tarea en segundo plano
        task = asyncio.create_task(process_documentation(
            url=url,
            language_code=data.language_code,
            analyze_subsections=data.analyze_subsections,
            max_depth=data.max_depth,
            excluded_paths=data.excluded_paths
        ))
        
        # Almacenar tarea para referencia futura
        background_tasks[url] = task
        
        # Obtener estado inicial
        status = await get_documentation_status(url)
        
        return status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al iniciar el procesamiento: {str(e)}")

@router.get("/scrape-status", response_model=DocumentStatusResponse)
async def check_documentation_status(url: str = Query(..., description="URL de la documentación")):
    """
    Consulta el estado actual del procesamiento de documentación.
    """
    try:
        status = await get_documentation_status(url)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener el estado: {str(e)}")

@router.post("/ask", response_model=DocumentQueryResponse)
async def query_documentation_endpoint(data: DocumentQueryInput):
    """
    Realiza una consulta sobre la documentación procesada.
    """
    try:
        # Verificar estado
        status = await get_documentation_status(str(data.url))
        if status["status"] != "completed":
            raise HTTPException(
                status_code=400, 
                detail=f"La documentación no está lista para consultas. Estado actual: {status['status']}"
            )
        
        # Realizar consulta
        result = await query_documentation(
            url=str(data.url),
            query=data.query,
            language_code=data.language_code,
            include_sources=data.include_sources
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al consultar la documentación: {str(e)}")

@router.delete("/scrape", response_model=dict)
async def cancel_documentation_processing(url: str = Query(..., description="URL de la documentación")):
    """
    Cancela el procesamiento de documentación en curso.
    """
    try:
        if url in background_tasks and not background_tasks[url].done():
            background_tasks[url].cancel()
            # Esperar a que la tarea sea cancelada
            try:
                await asyncio.wait_for(background_tasks[url], timeout=2.0)
            except asyncio.TimeoutError:
                pass  # La tarea puede no terminar limpiamente
            except asyncio.CancelledError:
                pass  # Esperado si la tarea fue cancelada
                
            return {"status": "cancelled", "url": url, "message": "Procesamiento cancelado correctamente"}
        else:
            return {"status": "not_found", "url": url, "message": "No se encontró un procesamiento activo para esta URL"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al cancelar el procesamiento: {str(e)}") 