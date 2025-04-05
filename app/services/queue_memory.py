import os
import time
import uuid
import threading
import asyncio
from typing import Dict, Any, Optional, List, Callable, Union
from datetime import datetime
import logging
import traceback
import json
from concurrent.futures import ThreadPoolExecutor

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Tiempo de expiración de trabajos en cola (3 días en segundos)
JOB_EXPIRATION = 259200  # 3 * 24 * 60 * 60 segundos

# Estado de los trabajos
JOB_STATUS_QUEUED = "queued"
JOB_STATUS_IN_PROGRESS = "in_progress"
JOB_STATUS_COMPLETED = "completed"
JOB_STATUS_FAILED = "failed"
JOB_STATUS_CANCELLED = "cancelled"

# Nombres de colas
QUEUE_DEFAULT = "default"
QUEUE_DOCS = "documentation"
QUEUE_HIGH = "high_priority"

# Almacenamiento en memoria para trabajos
jobs = {}
results = {}
queues = {
    QUEUE_DEFAULT: [],
    QUEUE_DOCS: [],
    QUEUE_HIGH: []
}

# Bloqueo para sincronización
lock = threading.RLock()

# Pool de threads para procesamiento
executor = ThreadPoolExecutor(max_workers=3)

# Función para generar ID único
def generate_job_id() -> str:
    """Genera un ID único para un trabajo."""
    return str(uuid.uuid4())

# Almacenar resultados
def store_result(key: str, result: Any, expiration: int = JOB_EXPIRATION) -> bool:
    """Almacena un resultado en memoria."""
    try:
        with lock:
            results[key] = {
                "result": result,
                "expiration": time.time() + expiration
            }
        return True
    except Exception as e:
        logger.error(f"Error almacenando resultado para {key}: {str(e)}")
        return False

# Recuperar resultados
def get_result(key: str) -> Optional[Any]:
    """Recupera un resultado de memoria."""
    try:
        with lock:
            if key in results:
                data = results[key]
                # Verificar expiración
                if data["expiration"] > time.time():
                    return data["result"]
                else:
                    # Eliminar resultados expirados
                    del results[key]
        return None
    except Exception as e:
        logger.error(f"Error recuperando resultado para {key}: {str(e)}")
        return None

# Ejecutar tarea asíncrona
def run_async_task(task_func, *args, **kwargs):
    """Ejecuta una tarea de forma asíncrona en un thread."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        # Si la tarea es una corrutina, ejecutarla en el loop de eventos
        if asyncio.iscoroutinefunction(task_func):
            return loop.run_until_complete(task_func(*args, **kwargs))
        # Si no es una corrutina, ejecutarla directamente
        else:
            return task_func(*args, **kwargs)
    finally:
        loop.close()

# Procesar un trabajo
def process_job(job_id: str):
    """Procesa un trabajo de la cola."""
    try:
        with lock:
            if job_id not in jobs:
                return
            
            job = jobs[job_id]
            job["status"] = JOB_STATUS_IN_PROGRESS
            job["started_at"] = datetime.now().isoformat()
        
        logger.info(f"Procesando trabajo {job_id}")
        
        # Ejecutar la función
        result = run_async_task(job["func"], *job["args"], **job["kwargs"])
        
        # Almacenar resultado
        with lock:
            if job_id in jobs:  # Verificar que el trabajo no haya sido cancelado
                job["result"] = result
                job["status"] = JOB_STATUS_COMPLETED
                job["ended_at"] = datetime.now().isoformat()
                logger.info(f"Trabajo {job_id} completado")
    except Exception as e:
        # Almacenar error
        error_msg = f"Error en trabajo {job_id}: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        
        with lock:
            if job_id in jobs:  # Verificar que el trabajo no haya sido cancelado
                job["status"] = JOB_STATUS_FAILED
                job["error"] = error_msg
                job["ended_at"] = datetime.now().isoformat()

# Encolar un trabajo
def enqueue_job(func, *args, queue_name: str = QUEUE_DEFAULT, job_id: Optional[str] = None, 
                job_timeout: int = 3600, **kwargs) -> Optional[str]:
    """
    Encola un trabajo para ejecución asíncrona.
    
    Args:
        func: Función a ejecutar
        *args: Argumentos para la función
        queue_name: Nombre de la cola
        job_id: ID opcional para el trabajo
        job_timeout: Tiempo máximo de ejecución en segundos
        **kwargs: Argumentos con nombre para la función
        
    Returns:
        ID del trabajo o None si falló
    """
    try:
        if job_id is None:
            job_id = generate_job_id()
            
        # Crear trabajo
        job = {
            "id": job_id,
            "func": func,
            "args": args,
            "kwargs": kwargs,
            "status": JOB_STATUS_QUEUED,
            "queue": queue_name,
            "timeout": job_timeout,
            "enqueued_at": datetime.now().isoformat(),
            "started_at": None,
            "ended_at": None,
            "result": None,
            "error": None
        }
        
        # Almacenar trabajo
        with lock:
            jobs[job_id] = job
            if queue_name not in queues:
                queues[queue_name] = []
            queues[queue_name].append(job_id)
        
        # Iniciar procesamiento en thread separado
        executor.submit(process_job, job_id)
        
        logger.info(f"Trabajo {job_id} encolado en {queue_name}")
        return job_id
    except Exception as e:
        logger.error(f"Error encolando trabajo: {str(e)}\n{traceback.format_exc()}")
        return None

# Cancelar un trabajo
def cancel_job(job_id: str) -> bool:
    """Cancela un trabajo en cola."""
    try:
        with lock:
            if job_id in jobs:
                job = jobs[job_id]
                
                # Solo se pueden cancelar trabajos en cola o en progreso
                if job["status"] in [JOB_STATUS_QUEUED, JOB_STATUS_IN_PROGRESS]:
                    job["status"] = JOB_STATUS_CANCELLED
                    job["ended_at"] = datetime.now().isoformat()
                    
                    # Eliminar de la cola si aún está ahí
                    queue_name = job["queue"]
                    if queue_name in queues and job_id in queues[queue_name]:
                        queues[queue_name].remove(job_id)
                        
                    logger.info(f"Trabajo {job_id} cancelado")
                    return True
        return False
    except Exception as e:
        logger.error(f"Error cancelando trabajo {job_id}: {str(e)}")
        return False

# Obtener estado de un trabajo
def get_job_status(job_id: str) -> Dict[str, Any]:
    """
    Obtiene el estado de un trabajo.
    
    Returns:
        Dict con información del estado del trabajo
    """
    try:
        with lock:
            if job_id not in jobs:
                return {
                    "job_id": job_id,
                    "status": "not_found",
                    "result": None,
                    "error": "Trabajo no encontrado"
                }
            
            job = jobs[job_id]
            
            return {
                "job_id": job_id,
                "status": job["status"],
                "queue": job["queue"],
                "enqueued_at": job["enqueued_at"],
                "started_at": job["started_at"],
                "ended_at": job["ended_at"],
                "result": job["result"],
                "error": job["error"]
            }
    except Exception as e:
        logger.error(f"Error obteniendo estado del trabajo {job_id}: {str(e)}")
        return {
            "job_id": job_id,
            "status": "error",
            "error": str(e)
        }

# Limpiar trabajos antiguos
def clean_old_jobs(days: int = 3) -> int:
    """
    Limpia trabajos antiguos de la memoria.
    
    Args:
        days: Trabajos más antiguos que este número de días serán eliminados
        
    Returns:
        Número de trabajos eliminados
    """
    try:
        count = 0
        cutoff_time = time.time() - (days * 24 * 60 * 60)
        
        with lock:
            # Eliminar trabajos completados o fallidos antiguos
            job_ids_to_remove = []
            for job_id, job in jobs.items():
                if job["status"] in [JOB_STATUS_COMPLETED, JOB_STATUS_FAILED, JOB_STATUS_CANCELLED]:
                    if job["ended_at"]:
                        # Convertir a timestamp para comparación
                        ended_timestamp = datetime.fromisoformat(job["ended_at"]).timestamp()
                        if ended_timestamp < cutoff_time:
                            job_ids_to_remove.append(job_id)
            
            # Eliminar trabajos
            for job_id in job_ids_to_remove:
                del jobs[job_id]
                # Eliminar de la cola si está presente
                for queue_name, queue_jobs in queues.items():
                    if job_id in queue_jobs:
                        queue_jobs.remove(job_id)
                count += 1
            
            # Limpiar resultados expirados
            result_keys_to_remove = []
            for key, data in results.items():
                if data["expiration"] < time.time():
                    result_keys_to_remove.append(key)
            
            for key in result_keys_to_remove:
                del results[key]
        
        return count
    except Exception as e:
        logger.error(f"Error limpiando trabajos antiguos: {str(e)}")
        return 0

# Iniciar limpieza periódica de trabajos
def start_cleanup_thread():
    """Inicia un thread para limpieza periódica de trabajos antiguos."""
    def cleanup_worker():
        while True:
            try:
                # Limpiar trabajos cada 6 horas
                time.sleep(6 * 60 * 60)
                count = clean_old_jobs()
                if count > 0:
                    logger.info(f"Limpieza periódica: {count} trabajos antiguos eliminados")
            except Exception as e:
                logger.error(f"Error en limpieza periódica: {str(e)}")
    
    # Iniciar thread
    cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
    cleanup_thread.start()

# Iniciar thread de limpieza
start_cleanup_thread() 