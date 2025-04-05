import os
from dotenv import load_dotenv
import requests
import json
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime
from typing import Dict, Any, List, Set, Optional
import traceback
import hashlib
import re
import numpy as np

# Importar servicios de embeddings
from app.services.embedding import (
    chunk_text, 
    generate_embedding_async, 
    generate_embeddings_batch_async,
    serialize_embedding,
    deserialize_embedding,
    search_by_similarity
)

# Para almacenamiento en memoria (en producción usaríamos una base de datos)
doc_cache = {}
doc_status = {}
doc_index = {}
doc_embeddings = {}  # Nuevo diccionario para almacenar embeddings

# Cargar variables de entorno
load_dotenv()

# API URLs y configuración
QWEN_API_URL = os.getenv("QWEN_API_URL", "http://localhost:8010/api/v1/services/aigc/text-generation/generation")
QWEN_API_KEY = os.getenv("QWEN_API_KEY")

# Número máximo de páginas que crawlear por dominio para evitar sobrecarga
MAX_PAGES = 50
# Tamaño máximo de cada trozo para embedding
CHUNK_SIZE = 512

def normalize_url(url: str) -> str:
    """Normaliza una URL para usarla como clave única."""
    parsed = urlparse(url)
    normalized = f"{parsed.netloc}{parsed.path}".rstrip('/')
    return normalized

def get_domain(url: str) -> str:
    """Extrae el dominio de una URL."""
    parsed = urlparse(url)
    return parsed.netloc

def generate_id(url: str) -> str:
    """Genera un ID único para una URL"""
    return hashlib.md5(url.encode()).hexdigest()

async def fetch_documentation(url: str) -> Dict[str, Any]:
    """
    Obtiene el contenido de la documentación desde una URL.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extraer el título
        title = soup.title.string if soup.title else url
        
        # Extraer el contenido principal
        # Intentamos encontrar el contenido principal usando selectores comunes
        main_content = (soup.find('main') or 
                      soup.find('article') or 
                      soup.find('div', {'id': 'content'}) or
                      soup.find('div', {'class': 'content'}) or
                      soup.find('div', {'class': 'documentation'}))
        
        if main_content:
            content = main_content.get_text(separator='\n', strip=True)
        else:
            # Si no encontramos el contenido principal, usamos todo el cuerpo
            content = soup.body.get_text(separator='\n', strip=True) if soup.body else ""
            
        # Extraer enlaces internos para crawling
        links = []
        base_domain = get_domain(url)
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            # Convertir URLs relativas a absolutas
            full_url = urljoin(url, href)
            # Solo añadir enlaces del mismo dominio y que sean HTML (no PDF, etc)
            if get_domain(full_url) == base_domain and not any(ext in full_url for ext in ['.pdf', '.zip', '.png', '.jpg', '.jpeg', '.gif']):
                links.append(full_url)
            
        return {
            "title": title,
            "content": content,
            "url": url,
            "links": links
        }
    except Exception as e:
        print(f"Error fetching documentation: {str(e)}")
        raise

async def crawl_documentation(
    base_url: str,
    max_depth: int = 3,
    excluded_paths: List[str] = []
) -> Dict[str, Dict[str, Any]]:
    """
    Realiza crawling de una documentación partiendo de una URL base.
    Retorna un diccionario de páginas analizadas.
    """
    try:
        pages = {}
        visited = set()
        to_visit = [(base_url, 0)]  # (url, depth)
        base_domain = get_domain(base_url)
        pages_count = 0
        
        # Compilar patrones de exclusión
        excluded_patterns = [re.compile(pattern) for pattern in excluded_paths]
        
        # Actualizar estado
        doc_id = generate_id(base_url)
        doc_status[doc_id] = {
            "url": base_url,
            "status": "in_progress",
            "sections_analyzed": 0,
            "total_pages": 1,  # Estimación inicial
            "completion_percentage": 0.0,
            "message": "Iniciando análisis de documentación..."
        }
        
        while to_visit and len(visited) < MAX_PAGES:
            current_url, depth = to_visit.pop(0)
            normalized_url = normalize_url(current_url)
            
            if normalized_url in visited:
                continue
                
            # Verificar patrones de exclusión
            if any(pattern.search(current_url) for pattern in excluded_patterns):
                continue
                
            visited.add(normalized_url)
            
            # Actualizar estado
            pages_count += 1
            doc_status[doc_id]["sections_analyzed"] = pages_count
            doc_status[doc_id]["completion_percentage"] = min(90.0, (pages_count / max(len(to_visit) + 1, 1)) * 100)
            doc_status[doc_id]["message"] = f"Analizando página: {current_url}"
            
            try:
                page_data = await fetch_documentation(current_url)
                pages[normalized_url] = page_data
                
                # Si no hemos alcanzado la profundidad máxima, añadir enlaces para visitar
                if depth < max_depth:
                    new_links = [(link, depth + 1) for link in page_data["links"] 
                               if normalize_url(link) not in visited]
                    to_visit.extend(new_links)
                    
                    # Actualizar total estimado de páginas
                    doc_status[doc_id]["total_pages"] = len(visited) + len(to_visit)
                    
                # Pequeña pausa para no sobrecargar el servidor
                await asyncio.sleep(0.5)
                
            except Exception as e:
                print(f"Error crawling {current_url}: {str(e)}")
                continue
        
        # Actualizar estado final de crawling
        doc_status[doc_id]["sections_analyzed"] = pages_count
        doc_status[doc_id]["total_pages"] = pages_count
        doc_status[doc_id]["completion_percentage"] = 90.0  # Reservamos 10% para procesamiento y embeddings
        doc_status[doc_id]["message"] = f"Finalizado crawling de {pages_count} páginas. Procesando información..."
            
        return pages
        
    except Exception as e:
        print(f"Error during crawling: {str(e)}\n{traceback.format_exc()}")
        raise

async def extract_key_info(content: str, language_code: str = "es") -> Dict[str, Any]:
    """
    Extrae información clave del contenido usando IA.
    """
    try:
        # Preparar el prompt para Qwen
        prompt = f"""Analiza la siguiente documentación y proporciona:
1. Un resumen conciso (máximo 3 párrafos)
2. Los conceptos clave más importantes (lista de 5-10 items)

Documentación:
{content[:20000]}  # Limitamos el contenido para no exceder los límites de la API

Responde en {language_code} y asegúrate de que el resumen sea claro y estructurado."""

        # Configurar la solicitud a Qwen
        payload = {
            "model": "qwen-max",
            "input": {
                "messages": [
                    {"role": "system", "content": "You are an expert in analyzing and summarizing technical documentation."},
                    {"role": "user", "content": prompt}
                ]
            },
            "parameters": {
                "result_format": "text",
                "max_tokens": 1500,
                "temperature": 0.7,
                "top_p": 0.8
            }
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {QWEN_API_KEY}"
        }

        # Hacer la solicitud a Qwen
        response = requests.post(
            QWEN_API_URL,
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        
        result = response.json()
        processed_text = result.get("output", {}).get("text", "")
        
        # Procesar la respuesta para extraer las secciones
        sections = processed_text.split('\n\n')
        summary = sections[0] if sections else ""
        key_concepts = []
        
        # Extraer conceptos clave (asumiendo que están en una sección específica)
        for section in sections:
            if "conceptos clave" in section.lower() or "key concepts" in section.lower():
                # Extraer conceptos clave como lista
                concept_lines = [line.strip() for line in section.split('\n') if line.strip()]
                # Eliminar la línea de encabezado
                if concept_lines and ("conceptos clave" in concept_lines[0].lower() or "key concepts" in concept_lines[0].lower()):
                    concept_lines = concept_lines[1:]
                # Limpiar cada concepto (quitar números o viñetas al inicio)
                key_concepts = [re.sub(r'^[0-9.•*-]+\s*', '', line) for line in concept_lines]
                break

        return {
            "summary": summary,
            "key_concepts": key_concepts
        }
        
    except Exception as e:
        print(f"Error extracting key info: {str(e)}")
        raise

async def create_vector_index(pages: Dict[str, Dict[str, Any]], doc_id: str) -> Dict[str, Any]:
    """
    Crea un índice de embeddings vectoriales para búsqueda semántica.
    """
    try:
        # Inicializar el índice y los embeddings
        index = {
            "pages": {},
            "keywords": {}  # Mantener para búsquedas por palabras clave de respaldo
        }
        
        # Creamos un espacio para almacenar los embeddings
        doc_embeddings[doc_id] = {
            "chunks": [],
            "texts": [],
            "page_urls": []
        }
        
        # Procesar página por página
        for url, page_data in pages.items():
            # Almacenar información de cada página
            index["pages"][url] = {
                "title": page_data["title"],
                "url": page_data["url"]
            }
            
            # Crear chunks del contenido
            content = page_data["content"]
            chunks = chunk_text(content, CHUNK_SIZE)
            
            if not chunks:
                continue
                
            # Generar embeddings para cada chunk
            chunk_embeddings = await generate_embeddings_batch_async(chunks)
            
            # Añadir los chunks y sus embeddings al índice
            for i, (chunk, embedding) in enumerate(zip(chunks, chunk_embeddings)):
                chunk_id = f"{url}_{i}"
                
                # Almacenar el embedding en memoria
                doc_embeddings[doc_id]["chunks"].append(chunk_id)
                doc_embeddings[doc_id]["texts"].append(chunk)
                doc_embeddings[doc_id]["page_urls"].append(url)
                
                # También actualizar el índice tradicional de palabras clave
                words = re.findall(r'\b\w+\b', chunk.lower())
                for word in words:
                    if len(word) > 3:  # Ignorar palabras muy cortas
                        if word not in index["keywords"]:
                            index["keywords"][word] = []
                        if url not in index["keywords"][word]:
                            index["keywords"][word].append(url)
        
        # Actualizar el estado
        doc_status[doc_id]["message"] = f"Índice vectorial creado: {len(doc_embeddings[doc_id]['chunks'])} chunks"
        doc_status[doc_id]["completion_percentage"] = 100.0
                
        return index
    
    except Exception as e:
        print(f"Error creating vector index: {str(e)}")
        # En producción, podrías querer volver al índice basado en palabras clave
        return {"pages": {p: {"title": pages[p]["title"], "url": pages[p]["url"]} for p in pages}, "keywords": {}}

async def process_documentation(
    url: str,
    language_code: str = "es",
    max_length: int = 1000,
    analyze_subsections: bool = True,
    max_depth: int = 3,
    excluded_paths: List[str] = []
) -> Dict[str, Any]:
    """
    Procesa la documentación completa, realizando crawling e indexación.
    """
    try:
        doc_id = generate_id(url)
        
        # Inicializar estado
        doc_status[doc_id] = {
            "url": url,
            "status": "in_progress",
            "sections_analyzed": 0,
            "total_pages": 1,
            "completion_percentage": 0.0,
            "message": "Iniciando análisis de documentación..."
        }
        
        # 1. Crawling de la documentación (si está habilitado)
        if analyze_subsections:
            pages = await crawl_documentation(url, max_depth, excluded_paths)
        else:
            # Si no se solicita crawling, solo procesar la página principal
            page_data = await fetch_documentation(url)
            normalized_url = normalize_url(url)
            pages = {normalized_url: page_data}
            
            # Actualizar estado
            doc_status[doc_id]["sections_analyzed"] = 1
            doc_status[doc_id]["total_pages"] = 1
            doc_status[doc_id]["completion_percentage"] = 50.0
            doc_status[doc_id]["message"] = "Analizando página principal..."
        
        # 2. Crear un único documento combinado para análisis (solo página principal para el resumen)
        main_page_data = pages[normalize_url(url)]
        
        # 3. Extraer información clave
        key_info = await extract_key_info(main_page_data["content"], language_code)
        
        # Actualizar estado
        doc_status[doc_id]["completion_percentage"] = 70.0
        doc_status[doc_id]["message"] = "Creando índice de búsqueda vectorial..."
        
        # 4. Crear índice para búsqueda (ahora con embeddings)
        index = await create_vector_index(pages, doc_id)
        
        # 5. También generar el embedding del resumen
        summary_embedding = await generate_embedding_async(key_info["summary"])
        
        # 6. Guardar en caché (en producción usaríamos una base de datos)
        doc_cache[doc_id] = {
            "url": url,
            "title": main_page_data["title"],
            "pages": pages,
            "summary": key_info["summary"],
            "key_concepts": key_info["key_concepts"],
            "processed_at": datetime.now().isoformat(),
            "summary_embedding": summary_embedding  # Añadir el embedding del resumen
        }
        
        # Guardar índice
        doc_index[doc_id] = index
        
        # Actualizar estado final
        doc_status[doc_id]["status"] = "completed"
        doc_status[doc_id]["completion_percentage"] = 100.0
        doc_status[doc_id]["message"] = f"Documentación analizada: {main_page_data['title']}"

        # Crear respuesta
        response = {
            "url": url,
            "title": main_page_data["title"],
            "summary": key_info["summary"],
            "key_concepts": key_info["key_concepts"],
            "processed_at": datetime.now().isoformat(),
            "sections_analyzed": len(pages),
            "total_pages": len(pages),
            "completion_percentage": 100.0,
            "status": "completed",
            "message": f"Documentación analizada: {main_page_data['title']}"
        }
        
        return response
        
    except Exception as e:
        # En caso de error, actualizar estado
        if doc_id in doc_status:
            doc_status[doc_id]["status"] = "failed"
            doc_status[doc_id]["message"] = f"Error: {str(e)}"
        
        print(f"Error processing documentation: {str(e)}\n{traceback.format_exc()}")
        raise

async def get_documentation_status(url: str) -> Dict[str, Any]:
    """
    Obtiene el estado actual del procesamiento de una documentación.
    """
    try:
        doc_id = generate_id(url)
        
        if doc_id not in doc_status:
            return {
                "url": url,
                "status": "not_found",
                "sections_analyzed": 0,
                "total_pages": 0,
                "completion_percentage": 0.0,
                "message": "La documentación no ha sido procesada o no se encontró"
            }
            
        return doc_status[doc_id]
        
    except Exception as e:
        print(f"Error getting documentation status: {str(e)}")
        raise

async def search_in_documentation(url: str, query: str) -> List[Dict[str, Any]]:
    """
    Busca una consulta en la documentación indexada utilizando embeddings vectoriales.
    Retorna los chunks más relevantes.
    """
    try:
        doc_id = generate_id(url)
        
        # Verificar que la documentación exista y tenga embeddings
        if doc_id not in doc_embeddings or not doc_embeddings[doc_id]["chunks"]:
            # Fallback a búsqueda por palabras clave
            return await search_by_keywords(url, query)
            
        # Generar embedding para la consulta
        query_embedding = await generate_embedding_async(query)
        
        # Reconstruir lista de embeddings desde la estructura en memoria
        embeddings = []
        for chunk_id in doc_embeddings[doc_id]["chunks"]:
            chunk_index = doc_embeddings[doc_id]["chunks"].index(chunk_id)
            embedding = await generate_embedding_async(doc_embeddings[doc_id]["texts"][chunk_index])
            embeddings.append(embedding)
        
        # Buscar por similitud
        search_results = search_by_similarity(
            query_embedding, 
            embeddings, 
            doc_embeddings[doc_id]["texts"],
            top_k=5
        )
        
        # Enriquecer los resultados con información de página
        for i, result in enumerate(search_results):
            chunk_index = doc_embeddings[doc_id]["texts"].index(result["text"])
            page_url = doc_embeddings[doc_id]["page_urls"][chunk_index]
            
            # Añadir información de la página
            if doc_id in doc_index and page_url in doc_index[doc_id]["pages"]:
                page_info = doc_index[doc_id]["pages"][page_url]
                result["url"] = page_url
                result["title"] = page_info["title"]
                
        return search_results
        
    except Exception as e:
        print(f"Error searching in documentation with vectors: {str(e)}")
        # Fallback a búsqueda por palabras clave
        return await search_by_keywords(url, query)

async def search_by_keywords(url: str, query: str) -> List[Dict[str, Any]]:
    """
    Método de respaldo que utiliza palabras clave en lugar de embeddings.
    """
    try:
        doc_id = generate_id(url)
        
        if doc_id not in doc_index:
            raise ValueError(f"La documentación {url} no ha sido indexada")
            
        index = doc_index[doc_id]
        pages = doc_cache[doc_id]["pages"]
        
        # Tokenizar la consulta
        query_words = set(re.findall(r'\b\w+\b', query.lower()))
        
        # Encontrar páginas relevantes (enfoque simple)
        page_scores = {}
        for word in query_words:
            if len(word) > 3 and word in index["keywords"]:
                for page_url in index["keywords"][word]:
                    if page_url not in page_scores:
                        page_scores[page_url] = 0
                    page_scores[page_url] += 1
        
        # Ordenar páginas por relevancia
        relevant_pages = sorted(
            [(url, score) for url, score in page_scores.items()],
            key=lambda x: x[1],
            reverse=True
        )
        
        # Retornar las 5 páginas más relevantes
        results = []
        for page_url, score in relevant_pages[:5]:
            normalized_url = normalize_url(page_url)
            if normalized_url in pages:
                page_data = pages[normalized_url]
                # Calcular relevancia normalizada
                relevance = min(score / max(len(query_words), 1), 1.0)
                
                # Crear extracto relevante
                content = page_data["content"]
                # Buscar párrafos que contengan palabras de la consulta
                paragraphs = content.split('\n')
                relevant_paragraphs = []
                
                for paragraph in paragraphs:
                    if any(word.lower() in paragraph.lower() for word in query_words if len(word) > 3):
                        relevant_paragraphs.append(paragraph)
                
                # Si no hay párrafos relevantes, usar los primeros párrafos
                if not relevant_paragraphs and paragraphs:
                    relevant_paragraphs = paragraphs[:2]
                
                # Crear un extracto de máximo 1000 caracteres
                excerpt = " ".join(relevant_paragraphs)[:1000] + "..."
                
                results.append({
                    "url": page_data["url"],
                    "title": page_data["title"],
                    "text": excerpt,
                    "similarity": relevance
                })
        
        return results
        
    except Exception as e:
        print(f"Error searching in documentation by keywords: {str(e)}")
        return []

async def query_documentation(
    url: str,
    query: str,
    language_code: str = "es",
    max_tokens: int = 2000,
    include_sources: bool = True
) -> Dict[str, Any]:
    """
    Realiza una consulta sobre la documentación procesada utilizando búsqueda vectorial.
    """
    try:
        # 1. Buscar los chunks más relevantes
        relevant_chunks = await search_in_documentation(url, query)
        
        if not relevant_chunks:
            # Si no hay chunks relevantes, usar la documentación principal
            doc_id = generate_id(url)
            if doc_id in doc_cache:
                main_page = doc_cache[doc_id]["pages"][normalize_url(url)]
                main_excerpt = main_page["content"][:5000] + "..."
                relevant_chunks = [{
                    "url": main_page["url"],
                    "title": main_page["title"],
                    "text": main_excerpt,
                    "similarity": 1.0
                }]
        
        # 2. Construir contexto para la IA
        context_text = ""
        sources = []
        
        for chunk in relevant_chunks:
            # Añadir el contenido de cada chunk relevante al contexto
            context_text += f"\n\nFuente: {chunk.get('title', 'Documento')} ({chunk.get('url', url)})\n{chunk['text']}"
            source_text = f"{chunk.get('title', 'Documento')} ({chunk.get('url', url)})"
            if source_text not in sources:
                sources.append(source_text)
            
        # 3. Generar prompt para Qwen
        prompt = f"""Responde a la siguiente pregunta basándote únicamente en la información proporcionada en el contexto:

Pregunta: {query}

Contexto:
{context_text[:30000]}

Proporciona una respuesta clara, completa y basada exclusivamente en la información del contexto.
Responde en {language_code}."""

        # 4. Configurar la solicitud a Qwen
        payload = {
            "model": "qwen-max",
            "input": {
                "messages": [
                    {"role": "system", "content": "You are an expert in answering questions based on technical documentation. Only use the provided context to answer, and be precise and accurate."},
                    {"role": "user", "content": prompt}
                ]
            },
            "parameters": {
                "result_format": "text",
                "max_tokens": max_tokens,
                "temperature": 0.5,  # Más bajo para respuestas más precisas
                "top_p": 0.9
            }
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {QWEN_API_KEY}"
        }

        # 5. Hacer la solicitud a Qwen
        response = requests.post(
            QWEN_API_URL,
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        
        result = response.json()
        answer = result.get("output", {}).get("text", "")
        
        # 6. Calcular nivel de confianza basado en la relevancia de las fuentes
        confidence = 0.0
        if relevant_chunks:
            avg_similarity = sum(chunk["similarity"] for chunk in relevant_chunks) / len(relevant_chunks)
            confidence = avg_similarity * 0.9  # Escalamos a max 0.9 para ser conservadores
        else:
            confidence = 0.5  # Confianza media si no hay chunks relevantes
        
        return {
            "answer": answer,
            "sources": sources if include_sources else [],
            "confidence": confidence
        }
        
    except Exception as e:
        print(f"Error querying documentation: {str(e)}\n{traceback.format_exc()}")
        raise 