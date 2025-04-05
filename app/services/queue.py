import os
import time
import json
import redis
import rq
from rq.job import Job
from typing import Dict, Any, Optional, List, Union
from redis import Redis
import asyncio
from datetime import datetime, timedelta
import logging
import uuid
import traceback

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar configuración de Redis desde variables de entorno o usar valores por defecto
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

# Tiempo de expiración de trabajos en cola (3 días)
JOB_EXPIRATION = 259200  # 3 * 24 * 60 * 60 segundos

# Nombres de colas
QUEUE_DEFAULT = "default"
QUEUE_DOCS = "documentation"
QUEUE_HIGH = "high_priority"

# Crear conexión a Redis
def get_redis_connection() -> Redis:
    """Obtiene la conexión a Redis."""
    try:
        conn = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            password=REDIS_PASSWORD,
            decode_responses=True,  # Para trabajar con strings en lugar de bytes
            socket_connect_timeout=5,
            socket_timeout=5
        )
        # Verificar conexión
        conn.ping()
        return conn
    except Exception as e:
        logger.error(f"Error conectando a Redis: {str(e)}")
        # En producción, podrías querer reintentar o fallar de manera más elegante
        raise

# Crear colas
def get_queue(queue_name: str = QUEUE_DEFAULT) -> rq.Queue:
    """Obtiene una cola RQ."""
    try:
        conn = get_redis_connection()
        return rq.Queue(name=queue_name, connection=conn, default_timeout=3600)
    except Exception as e:
        logger.error(f"Error creando cola {queue_name}: {str(e)}")
        raise

# Obtener trabajo por ID
def get_job(job_id: str, queue_name: str = QUEUE_DEFAULT) -> Optional[Job]:
    """Obtiene un trabajo por su ID."""
    try:
        conn = get_redis_connection()
        return Job.fetch(job_id, connection=conn)
    except rq.exceptions.NoSuchJobError:
        return None
    except Exception as e:
        logger.error(f"Error obteniendo trabajo {job_id}: {str(e)}")
        return None

# Almacenar resultados en Redis (para resultados grandes)
def store_result(key: str, result: Any, expiration: int = JOB_EXPIRATION) -> bool:
    """Almacena un resultado en Redis."""
    try:
        conn = get_redis_connection()
        serialized = json.dumps(result)
        conn.set(f"result:{key}", serialized, ex=expiration)
        return True
    except Exception as e:
        logger.error(f"Error almacenando resultado para {key}: {str(e)}")
        return False

# Recuperar resultados de Redis
def get_result(key: str) -> Optional[Any]:
    """Recupera un resultado de Redis."""
    try:
        conn = get_redis_connection()
        serialized = conn.get(f"result:{key}")
        if serialized:
            return json.loads(serialized)
        return None
    except Exception as e:
        logger.error(f"Error recuperando resultado para {key}: {str(e)}")
        return None

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
        queue = get_queue(queue_name)
        if not job_id:
            job_id = str(uuid.uuid4())
        
        job = queue.enqueue(
            func,
            *args,
            **kwargs,
            job_id=job_id,
            result_ttl=JOB_EXPIRATION,
            failure_ttl=JOB_EXPIRATION,
            ttl=JOB_EXPIRATION,
            timeout=job_timeout
        )
        
        return job.id
    except Exception as e:
        logger.error(f"Error encolando trabajo: {str(e)}\n{traceback.format_exc()}")
        return None

# Cancelar un trabajo
def cancel_job(job_id: str) -> bool:
    """Cancela un trabajo en cola."""
    try:
        job = get_job(job_id)
        if job:
            if job.is_queued or job.is_started:
                job.cancel()
                job.delete()
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
        job = get_job(job_id)
        if not job:
            return {
                "job_id": job_id,
                "status": "not_found",
                "result": None,
                "error": "Trabajo no encontrado"
            }
        
        status = "unknown"
        if job.is_queued:
            status = "queued"
        elif job.is_started:
            status = "in_progress"
        elif job.is_finished:
            status = "completed"
        elif job.is_failed:
            status = "failed"
        
        result = None
        error = None
        
        if job.is_finished:
            result = job.result
        
        if job.is_failed:
            if hasattr(job, "exc_info") and job.exc_info:
                error = job.exc_info
            else:
                error = "Error desconocido en el trabajo"
        
        return {
            "job_id": job_id,
            "status": status,
            "queue": job.origin,
            "enqueued_at": job.enqueued_at.isoformat() if job.enqueued_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "ended_at": job.ended_at.isoformat() if job.ended_at else None,
            "result": result,
            "error": error
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
    Limpia trabajos antiguos de Redis.
    
    Args:
        days: Trabajos más antiguos que este número de días serán eliminados
        
    Returns:
        Número de trabajos eliminados
    """
    try:
        conn = get_redis_connection()
        count = 0
        
        # Limpiar colas conocidas
        for queue_name in [QUEUE_DEFAULT, QUEUE_DOCS, QUEUE_HIGH]:
            queue = rq.Queue(name=queue_name, connection=conn)
            cutoff = datetime.now() - timedelta(days=days)
            
            # Eliminar trabajos fallidos
            registry = rq.registry.FailedJobRegistry(queue=queue)
            for job_id in registry.get_job_ids():
                job = Job.fetch(job_id, connection=conn)
                if job.ended_at and job.ended_at < cutoff:
                    job.delete()
                    count += 1
            
            # Eliminar trabajos completados
            registry = rq.registry.FinishedJobRegistry(queue=queue)
            for job_id in registry.get_job_ids():
                job = Job.fetch(job_id, connection=conn)
                if job.ended_at and job.ended_at < cutoff:
                    job.delete()
                    count += 1
        
        return count
    except Exception as e:
        logger.error(f"Error limpiando trabajos antiguos: {str(e)}")
        return 0 