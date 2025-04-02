import os
from dotenv import load_dotenv
import requests
import json
from urllib.parse import urlparse, parse_qs
from typing import Optional, Dict, Any

from .transcription import get_video_transcript, get_video_id

# Cargar variables de entorno
load_dotenv()

# Mapeo de códigos de idioma a nombres completos
LANGUAGE_MAP = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "zh": "Chinese",
    "ja": "Japanese",
    "ko": "Korean",
    "ru": "Russian"
}

# API URLs y configuración
# Obtener la URL del API de las variables de entorno con un valor predeterminado
# para desarrollo local (proxy)
QWEN_API_URL = os.getenv("QWEN_API_URL", "http://localhost:8010/api/v1/services/aigc/text-generation/generation")
QWEN_API_KEY = os.getenv("QWEN_API_KEY")

# Verificar la clave API y URL (para depuración)
print(f"API Key: {QWEN_API_KEY[:5] if QWEN_API_KEY else 'No encontrada'}... (primeros 5 caracteres)")
print(f"Usando URL: {QWEN_API_URL}")

async def generate_summary_from_text(
    text: str,
    language_code: str = "es",
    max_length: int = 500
) -> str:
    """
    Genera un resumen de un texto utilizando Qwen API.
    
    Args:
        text: Texto a resumir
        language_code: Código del idioma para la respuesta
        max_length: Longitud máxima del resumen en tokens
        
    Returns:
        El resumen generado
    """
    try:
        # Verificar la longitud del texto y truncar si es necesario
        # Qwen API tiene un límite de 30,720 caracteres
        if not text or len(text) == 0:
            return "No hay texto para resumir."
            
        original_length = len(text)
        max_api_length = 30000  # Un poco menos que el límite de 30,720 para margen de seguridad
        
        if len(text) > max_api_length:
            print(f"Texto demasiado largo ({original_length} caracteres), truncando a {max_api_length} caracteres")
            text = text[:max_api_length]
            
        # Formato para el proxy local, como en el otro proyecto
        payload = {
            "model": "qwen-max",
            "input": {
                "messages": [
                    {"role": "system", "content": "You are an expert assistant in summarizing content."},
                    {"role": "user", "content": f"Generate a summary of the following text in {LANGUAGE_MAP.get(language_code, 'English')}, maximum {max_length} tokens:\n\n{text}"}
                ]
            },
            "parameters": {
                "result_format": "text",
                "max_tokens": max_length,
                "temperature": 0.7,
                "top_p": 0.8
            }
        }
        
        # Encabezados similares al otro proyecto
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {QWEN_API_KEY}"
        }
        
        print(f"URL: {QWEN_API_URL}")
        print(f"Encabezados: Content-Type={headers['Content-Type']}")
        print(f"Primeros 5 caracteres del token: {QWEN_API_KEY[:5]}...")
        print(f"Longitud del texto a resumir: {len(text)} caracteres")
        print("Enviando solicitud a proxy local de Qwen API...")
        
        # Hacer la solicitud
        response = requests.post(
            QWEN_API_URL,
            headers=headers,
            json=payload
        )
        
        # Verificar si la solicitud fue exitosa
        if response.status_code == 200:
            print("Respuesta exitosa del API")
            result = response.json()
            if "output" in result and "text" in result["output"]:
                return result["output"]["text"]
            else:
                print(f"Estructura de respuesta inesperada: {result}")
                return f"No se pudo extraer el texto del resumen. Respuesta: {result}"
        else:
            print(f"Código de error: {response.status_code}")
            print(f"Respuesta completa: {response.text}")
            
            # Generar resumen fallback para cualquier error
            error_msg = f"Error al obtener resumen (código {response.status_code}): {response.text}"
            print(error_msg)
            
            # Crear un resumen fallback basado en las primeras líneas
            return _generate_fallback_summary(text, error_msg)
        
    except Exception as e:
        # Si hay un error con Qwen, generar un resumen simulado
        print(f"Error al generar resumen con Qwen: {str(e)}")
        return _generate_fallback_summary(text, str(e))

def _generate_fallback_summary(text: str, error_reason: str) -> str:
    """Genera un resumen fallback basado en las primeras líneas del texto"""
    lines = text.split('\n')
    summary_lines = []
    total_lines = min(5, len(lines))
    
    for i in range(total_lines):
        if lines[i].strip():  # Solo agregar líneas no vacías
            summary_lines.append(lines[i])
    
    summary = f"Resumen automático (debido a un error en la generación con IA: {error_reason}):\n\n"
    summary += "\n".join(summary_lines)
    summary += "\n\n(Resumen parcial basado en las primeras líneas del texto)"
    
    return summary

async def generate_summary(
    video_url: Optional[str] = None,
    transcription: Optional[str] = None,
    language_code: str = "es",
    max_length: int = 500
) -> Dict[str, Any]:
    """
    Genera un resumen basado en una URL de YouTube o una transcripción directa.
    
    Args:
        video_url: URL del video de YouTube (opcional si se proporciona transcripción)
        transcription: Transcripción directa del contenido (opcional si se proporciona video_url)
        language_code: Código del idioma para la transcripción/respuesta
        max_length: Longitud máxima del resumen en tokens
        
    Returns:
        Diccionario con el resumen, ID del video (si aplica) y URL (si aplica)
    """
    try:
        video_id = None
        transcript = None
        
        # Si se proporciona una transcripción directa, usarla
        if transcription:
            transcript = transcription
        # Si se proporciona una URL, obtener la transcripción del video
        elif video_url:
            # Obtener el ID del video
            video_id = get_video_id(video_url)
            
            # Obtener la transcripción del video
            transcript = await get_video_transcript(
                video_url=video_url,
                language_code=language_code
            )
        else:
            raise ValueError("Debe proporcionar una URL de video o una transcripción")
        
        if not transcript:
            return {
                "summary": "No se pudo obtener texto para resumir. Es posible que el video no tenga transcripción disponible.",
                "video_id": video_id,
                "video_url": video_url
            }
        
        # Generar el resumen del texto
        summary = await generate_summary_from_text(
            text=transcript,
            language_code=language_code,
            max_length=max_length
        )
        
        return {
            "summary": summary,
            "video_id": video_id,
            "video_url": video_url
        }
    except Exception as e:
        error_message = f"Error al generar el resumen: {str(e)}"
        print(error_message)
        
        # Generar un resumen emergencia para evitar errores de validación
        emergency_summary = "No se pudo generar el resumen debido a un error en el servidor. "
        if transcription and len(transcription) > 0:
            lines = transcription.split('\n')
            if len(lines) > 0:
                emergency_summary += f"El texto comienza con: {lines[0][:100]}..."
        
        return {
            "summary": emergency_summary,
            "video_id": video_id if video_id else "unknown",
            "video_url": video_url
        } 