import os
import numpy as np
import pickle
from typing import List, Dict, Any, Optional, Union
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import re
import asyncio
from concurrent.futures import ThreadPoolExecutor
import gc

# Modelo de embedding, se cargará bajo demanda
model = None
executor = ThreadPoolExecutor(max_workers=1)  # Limitamos a 1 worker para evitar problemas de memoria

# Nombre/ruta del modelo a utilizar (podemos cambiar por uno multilingüe si es necesario)
# MODEL_NAME = os.getenv("EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")
MODEL_NAME = os.getenv("EMBEDDING_MODEL", "paraphrase-MiniLM-L3-v2")

def get_model():
    """
    Carga el modelo de embedding bajo demanda.
    Reutiliza la instancia si ya está cargada.
    """
    global model
    if model is None:
        try:
            model = SentenceTransformer(MODEL_NAME)
            print(f"Modelo de embeddings cargado: {MODEL_NAME}")
        except Exception as e:
            print(f"Error al cargar el modelo de embeddings: {str(e)}")
            raise
    return model

def cleanup_model():
    """
    Libera memoria descargando el modelo cuando no se necesita.
    Útil para entornos con recursos limitados.
    """
    global model
    if model is not None:
        del model
        model = None
        gc.collect()
        print("Modelo de embeddings liberado")

def chunk_text(text: str, max_length: int = 512) -> List[str]:
    """
    Divide un texto largo en chunks más pequeños para procesar.
    Los chunks respetan los límites de párrafos cuando es posible.
    """
    if not text or not isinstance(text, str):
        return []
        
    # Dividir por párrafos
    paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
    
    chunks = []
    current_chunk = ""
    
    for paragraph in paragraphs:
        # Si el párrafo es muy largo, dividirlo en oraciones
        if len(paragraph) > max_length:
            sentences = re.split(r'(?<=[.!?])\s+', paragraph)
            for sentence in sentences:
                if len(current_chunk) + len(sentence) + 1 <= max_length:
                    current_chunk += " " + sentence if current_chunk else sentence
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = sentence
        else:
            # Si añadir el párrafo completo no excede el límite, añadirlo
            if len(current_chunk) + len(paragraph) + 1 <= max_length:
                current_chunk += " " + paragraph if current_chunk else paragraph
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = paragraph
    
    # Añadir el último chunk si existe
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks

def generate_embedding(text: str) -> np.ndarray:
    """
    Genera un embedding para un texto dado.
    """
    if not text or not isinstance(text, str):
        # Devolver un vector de ceros si el texto es inválido
        return np.zeros(384)  # Dimensión típica de los modelos MiniLM
        
    try:
        model = get_model()
        embedding = model.encode(text, convert_to_numpy=True)
        return embedding
    except Exception as e:
        print(f"Error generando embedding: {str(e)}")
        return np.zeros(384)  # Vector de ceros como fallback

def generate_embeddings_batch(texts: List[str]) -> List[np.ndarray]:
    """
    Genera embeddings para una lista de textos en batch.
    Más eficiente que generarlos uno por uno.
    """
    if not texts:
        return []
        
    try:
        model = get_model()
        embeddings = model.encode(texts, convert_to_numpy=True, batch_size=32)
        return embeddings
    except Exception as e:
        print(f"Error generando embeddings batch: {str(e)}")
        return [np.zeros(384) for _ in texts]  # Vectores de ceros como fallback

async def generate_embedding_async(text: str) -> np.ndarray:
    """
    Versión asíncrona de la generación de embeddings.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, generate_embedding, text)

async def generate_embeddings_batch_async(texts: List[str]) -> List[np.ndarray]:
    """
    Versión asíncrona de la generación de embeddings en batch.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, generate_embeddings_batch, texts)

def serialize_embedding(embedding: np.ndarray) -> bytes:
    """
    Serializa un embedding para almacenarlo en la base de datos.
    """
    return pickle.dumps(embedding)

def deserialize_embedding(serialized_embedding: bytes) -> np.ndarray:
    """
    Deserializa un embedding desde la base de datos.
    """
    if not serialized_embedding:
        return np.zeros(384)
    return pickle.loads(serialized_embedding)

def search_by_similarity(query_embedding: np.ndarray, embeddings: List[np.ndarray], texts: List[str], top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Busca los textos más similares a una consulta usando similitud de coseno.
    
    Args:
        query_embedding: Embedding de la consulta
        embeddings: Lista de embeddings a comparar
        texts: Lista de textos correspondientes a los embeddings
        top_k: Número de resultados a devolver
        
    Returns:
        Lista de diccionarios con texto y puntuación de similitud
    """
    if not embeddings or len(embeddings) != len(texts):
        return []
    
    # Calcular similitud de coseno entre la consulta y todos los embeddings
    similarities = cosine_similarity([query_embedding], embeddings)[0]
    
    # Ordenar por similitud y obtener los índices de los top_k
    top_indices = np.argsort(similarities)[::-1][:top_k]
    
    # Construir resultados
    results = [
        {
            "text": texts[idx],
            "similarity": float(similarities[idx]),
        }
        for idx in top_indices
    ]
    
    return results 