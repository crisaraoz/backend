import os
from dotenv import load_dotenv
import requests
import json
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Dict, Any, List
import traceback

# Cargar variables de entorno
load_dotenv()

# API URLs y configuración
QWEN_API_URL = os.getenv("QWEN_API_URL", "http://localhost:8010/api/v1/services/aigc/text-generation/generation")
QWEN_API_KEY = os.getenv("QWEN_API_KEY")

async def fetch_documentation(url: str) -> Dict[str, Any]:
    """
    Obtiene el contenido de la documentación desde una URL.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extraer el título
        title = soup.title.string if soup.title else url
        
        # Extraer el contenido principal
        # Asumimos que el contenido principal está en el elemento main o article
        main_content = soup.find('main') or soup.find('article')
        if main_content:
            content = main_content.get_text(separator='\n', strip=True)
        else:
            content = soup.get_text(separator='\n', strip=True)
            
        return {
            "title": title,
            "content": content,
            "url": url
        }
    except Exception as e:
        print(f"Error fetching documentation: {str(e)}")
        raise

async def process_documentation(
    url: str,
    language_code: str = "es",
    max_length: int = 1000
) -> Dict[str, Any]:
    """
    Procesa la documentación y genera un resumen con conceptos clave.
    """
    try:
        # Obtener el contenido de la documentación
        doc_content = await fetch_documentation(url)
        
        # Preparar el prompt para Qwen
        prompt = f"""Analiza la siguiente documentación y proporciona:
1. Un resumen conciso
2. Los conceptos clave más importantes
3. La estructura principal

Documentación:
{doc_content['content'][:30000]}  # Limitamos el contenido para no exceder los límites de la API

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
                "max_tokens": max_length,
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
                key_concepts = [item.strip() for item in section.split('\n') if item.strip()]
                break

        return {
            "url": url,
            "title": doc_content["title"],
            "summary": summary,
            "key_concepts": key_concepts,
            "processed_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"Error processing documentation: {str(e)}\n{traceback.format_exc()}")
        raise

async def query_documentation(
    doc_id: str,
    query: str,
    language_code: str = "es"
) -> Dict[str, Any]:
    """
    Realiza una consulta sobre la documentación procesada.
    """
    try:
        # Aquí deberías recuperar la documentación procesada de tu base de datos
        # Por ahora, simularemos una respuesta
        prompt = f"""Basado en la siguiente consulta sobre la documentación, proporciona una respuesta detallada:

Consulta: {query}

Responde en {language_code} y asegúrate de incluir ejemplos o referencias específicas cuando sea posible."""

        payload = {
            "model": "qwen-max",
            "input": {
                "messages": [
                    {"role": "system", "content": "You are an expert in technical documentation and can provide detailed answers based on documentation content."},
                    {"role": "user", "content": prompt}
                ]
            },
            "parameters": {
                "result_format": "text",
                "max_tokens": 1000,
                "temperature": 0.7,
                "top_p": 0.8
            }
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {QWEN_API_KEY}"
        }

        response = requests.post(
            QWEN_API_URL,
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        
        result = response.json()
        answer = result.get("output", {}).get("text", "")

        return {
            "answer": answer,
            "relevant_sections": [],  # Aquí deberías incluir las secciones relevantes
            "confidence": 0.85  # Este valor debería calcularse basado en la relevancia
        }
        
    except Exception as e:
        print(f"Error querying documentation: {str(e)}\n{traceback.format_exc()}")
        raise 