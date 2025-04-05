import os
import sys
import time
import asyncio
import logging
from typing import Dict, Any, Optional, List
import traceback
import json

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Importar servicios
from app.services.docs import (
    process_documentation,
    get_documentation_status,
    query_documentation,
    generate_id
)

# Importar nuestro sistema de colas en memoria
from app.services.queue_memory import (
    store_result,
    get_result
)

# Para ejecutar funciones asíncronas en un entorno síncrono
def run_async(coro):
    """Ejecuta una corrutina en un entorno síncrono."""
    # Verificar si ya estamos en un evento loop
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Si el loop está corriendo, usamos asyncio.run_coroutine_threadsafe
            # pero como estamos en un entorno síncrono, esperamos el resultado
            future = asyncio.run_coroutine_threadsafe(coro, loop)
            return future.result()
    except RuntimeError:
        # No hay un evento loop en este thread
        pass
        
    # Crear un nuevo evento loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

# Tarea para procesar documentación
def process_doc_task(
    url: str,
    language_code: str = "es",
    max_length: int = 1000,
    analyze_subsections: bool = True,
    max_depth: int = 3,
    excluded_paths: List[str] = []
) -> Dict[str, Any]:
    """
    Tarea para procesar documentación de forma asíncrona.
    Esta tarea será ejecutada por el worker.
    """
    try:
        logger.info(f"Iniciando procesamiento de documentación: {url}")
        
        # Ejecutar la función asíncrona en un entorno síncrono
        result = run_async(process_documentation(
            url=url,
            language_code=language_code,
            max_length=max_length,
            analyze_subsections=analyze_subsections,
            max_depth=max_depth,
            excluded_paths=excluded_paths
        ))
        
        logger.info(f"Procesamiento completado para: {url}")
        
        # En caso de resultados grandes, almacenarlos 
        doc_id = generate_id(url)
        if sys.getsizeof(json.dumps(result)) > 10000:  # Si es mayor a ~10KB
            logger.info(f"Almacenando resultado grande para: {url}")
            success = store_result(f"doc_process:{doc_id}", result)
            if success:
                return {"stored_key": f"doc_process:{doc_id}", "status": "completed"}
        
        return result
    except Exception as e:
        error_msg = f"Error procesando documentación {url}: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        
        # Actualizar estado en caso de error
        try:
            doc_id = generate_id(url)
            run_async(update_doc_status(
                doc_id=doc_id,
                status="failed",
                message=f"Error: {str(e)}"
            ))
        except Exception as update_error:
            logger.error(f"Error actualizando estado: {str(update_error)}")
        
        # Retransmitir el error para que sea manejado
        raise

# Actualizar estado de procesamiento
async def update_doc_status(
    doc_id: str,
    status: str,
    message: str = "",
    completion_percentage: float = None,
    sections_analyzed: int = None,
    total_pages: int = None
) -> Dict[str, Any]:
    """
    Actualiza el estado de procesamiento de una documentación.
    Esta función es llamada por el task y por la API para actualizar
    el progreso.
    """
    try:
        # Obtener el estado actual
        current_status = await get_documentation_status(doc_id)
        
        # Actualizar solo los campos proporcionados
        if status:
            current_status["status"] = status
        if message:
            current_status["message"] = message
        if completion_percentage is not None:
            current_status["completion_percentage"] = completion_percentage
        if sections_analyzed is not None:
            current_status["sections_analyzed"] = sections_analyzed
        if total_pages is not None:
            current_status["total_pages"] = total_pages
            
        return current_status
    except Exception as e:
        logger.error(f"Error actualizando estado de {doc_id}: {str(e)}")
        raise

# Tarea para consultar documentación
def query_doc_task(
    url: str,
    query: str,
    language_code: str = "es",
    max_tokens: int = 2000,
    include_sources: bool = True
) -> Dict[str, Any]:
    """
    Tarea para realizar consultas a la documentación de forma asíncrona.
    Esta tarea será ejecutada por el sistema de colas.
    """
    try:
        logger.info(f"Iniciando consulta a documentación: {url}, Query: {query}")
        
        # Ejecutar la función asíncrona en un entorno síncrono
        result = run_async(query_documentation(
            url=url,
            query=query,
            language_code=language_code,
            max_tokens=max_tokens,
            include_sources=include_sources
        ))
        
        logger.info(f"Consulta completada para: {url}")
        return result
    except Exception as e:
        error_msg = f"Error consultando documentación {url}: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        raise 