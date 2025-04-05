import os
import sys
import time
import logging
import argparse
from redis import Redis
import rq
from rq import Worker, Queue, Connection
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("worker.log")
    ]
)

logger = logging.getLogger("worker")

# Cargar configuración de Redis desde variables de entorno o usar valores por defecto
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

# Nombres de colas
DEFAULT_QUEUES = ['documentation', 'high_priority', 'default']

def get_redis_connection():
    return Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        password=REDIS_PASSWORD
    )

def start_worker(queues=None, name=None):
    """Inicia un worker para procesar trabajos de las colas especificadas."""
    if queues is None:
        queues = DEFAULT_QUEUES
    
    if name is None:
        name = f"worker-{os.getpid()}"
    
    try:
        logger.info(f"Iniciando worker '{name}' para colas: {', '.join(queues)}")
        
        with Connection(get_redis_connection()):
            worker = Worker(
                queues=[Queue(queue_name) for queue_name in queues],
                name=name
            )
            worker.work(with_scheduler=True)
    except KeyboardInterrupt:
        logger.info(f"Worker '{name}' detenido por usuario")
    except Exception as e:
        logger.error(f"Error en worker '{name}': {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Worker para procesamiento de tareas asíncronas")
    parser.add_argument(
        "--queues", 
        nargs="+", 
        default=DEFAULT_QUEUES,
        help="Colas a monitorear (en orden de prioridad)"
    )
    parser.add_argument(
        "--name",
        type=str,
        default=None,
        help="Nombre para el worker"
    )
    
    args = parser.parse_args()
    start_worker(queues=args.queues, name=args.name) 