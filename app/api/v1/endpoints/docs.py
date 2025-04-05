from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl
from typing import List, Dict, Any, Optional
import asyncio
import time
import uuid
from app.services.docs import (
    generate_id,
    get_documentation_status,
    query_documentation
)
# Importar nuestro sistema de colas en memoria en lugar de Redis
from app.services.queue_memory import (
    enqueue_job,
    get_job_status,
    cancel_job,
    QUEUE_DOCS,
    get_result
)
from app.tasks.doc_tasks import (
    process_doc_task,
    query_doc_task
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
    job_id: Optional[str] = None

class DocumentQueryInput(BaseModel):
    url: HttpUrl
    query: str
    language_code: str = "es"
    include_sources: bool = True

class DocumentQueryResponse(BaseModel):
    answer: str
    sources: List[str] = []
    confidence: float

# Diccionario para almacenar la relación entre URLs y trabajos
doc_jobs = {}

@router.post("/scrape", response_model=DocumentStatusResponse)
async def start_documentation_processing(data: DocumentUrlInput):
    """
    Inicia el procesamiento de documentación en segundo plano usando el sistema de colas.
    Retorna de inmediato con el estado inicial.
    """
    try:
        url = str(data.url)
        doc_id = generate_id(url)
        
        # Verificar si ya existe un trabajo para esta URL
        if url in doc_jobs:
            # Verificar estado del trabajo existente
            job_status = get_job_status(doc_jobs[url])
            if job_status["status"] in ["queued", "in_progress"]:
                # Si el trabajo todavía está en proceso, retornar su estado actual
                status = await get_documentation_status(url)
                status["job_id"] = doc_jobs[url]
                return status
        
        # Encolar el trabajo en la cola de documentación
        job_id = enqueue_job(
            process_doc_task,
            url=url,
            language_code=data.language_code,
            analyze_subsections=data.analyze_subsections,
            max_depth=data.max_depth,
            excluded_paths=data.excluded_paths,
            queue_name=QUEUE_DOCS,
            job_timeout=7200  # 2 horas máximo
        )
        
        if not job_id:
            raise HTTPException(
                status_code=500,
                detail="Error al encolar el trabajo de procesamiento"
            )
        
        # Almacenar la relación entre la URL y el trabajo
        doc_jobs[url] = job_id
        
        # Obtener estado inicial
        status = await get_documentation_status(url)
        status["job_id"] = job_id
        
        return status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al iniciar el procesamiento: {str(e)}")

@router.get("/scrape-status", response_model=DocumentStatusResponse)
async def check_documentation_status(url: str = Query(..., description="URL de la documentación")):
    """
    Consulta el estado actual del procesamiento de documentación.
    Primero verifica el estado en el sistema de colas y luego en el servicio de documentación.
    """
    try:
        doc_id = generate_id(url)
        status = await get_documentation_status(url)
        
        # Si hay un trabajo asociado, obtener su estado
        if url in doc_jobs:
            job_id = doc_jobs[url]
            job_status = get_job_status(job_id)
            
            # Actualizar el estado según el trabajo
            if job_status["status"] == "completed":
                # Si el trabajo ha terminado con éxito
                status["status"] = "completed"
                status["job_id"] = job_id
                
                # Verificar si el resultado está almacenado por separado
                if "result" in job_status and job_status["result"]:
                    if isinstance(job_status["result"], dict) and "stored_key" in job_status["result"]:
                        # Recuperar el resultado grande 
                        stored_result = get_result(job_status["result"]["stored_key"])
                        if stored_result:
                            # Actualizar el estado con la información del resultado
                            status.update(stored_result)
            
            elif job_status["status"] == "failed":
                # Si el trabajo ha fallado
                status["status"] = "failed"
                status["message"] = f"Error: {job_status.get('error', 'Error desconocido')}"
                status["job_id"] = job_id
            
            else:
                # Si el trabajo está en proceso o en cola
                status["job_id"] = job_id
        
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener el estado: {str(e)}")

@router.post("/ask", response_model=DocumentQueryResponse)
async def query_documentation_endpoint(data: DocumentQueryInput):
    """
    Realiza una consulta sobre la documentación procesada.
    Para consultas complejas, puede usar el sistema de colas para procesamiento asíncrono.
    """
    try:
        url = str(data.url)
        
        # Verificar estado
        status = await get_documentation_status(url)
        if status["status"] != "completed":
            raise HTTPException(
                status_code=400, 
                detail=f"La documentación no está lista para consultas. Estado actual: {status['status']}"
            )
        
        # Para consultas simples, responder de inmediato
        # Para consultas complejas, podríamos encolar un trabajo, pero por ahora lo hacemos síncrono
        result = await query_documentation(
            url=url,
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
        if url in doc_jobs:
            job_id = doc_jobs[url]
            
            # Cancelar el trabajo en la cola
            cancelled = cancel_job(job_id)
            
            if cancelled:
                # Actualizar el estado
                doc_id = generate_id(url)
                status = await get_documentation_status(url)
                status["status"] = "cancelled"
                status["message"] = "Procesamiento cancelado por el usuario"
                
                return {
                    "status": "cancelled", 
                    "url": url, 
                    "message": "Procesamiento cancelado correctamente",
                    "job_id": job_id
                }
            else:
                return {
                    "status": "not_cancelled", 
                    "url": url, 
                    "message": "No se pudo cancelar el procesamiento",
                    "job_id": job_id
                }
        else:
            return {
                "status": "not_found", 
                "url": url, 
                "message": "No se encontró un procesamiento activo para esta URL"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al cancelar el procesamiento: {str(e)}") 