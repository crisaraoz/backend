from fastapi import APIRouter, HTTPException
from app.schemas.summary import SummaryRequest, SummaryResponse
from app.services.summary import generate_summary
from app.services.transcription import get_video_transcript, get_video_id
from pydantic import BaseModel
from typing import Optional
import traceback

router = APIRouter()

class TranscriptionAndSummaryRequest(BaseModel):
    url: str
    language_code: Optional[str] = "es"
    max_length: Optional[int] = 500

class TranscriptionAndSummaryResponse(BaseModel):
    transcription: str
    summary: str
    video_id: str
    video_url: str

@router.post("/youtube", response_model=SummaryResponse)
async def summarize_youtube_video(request: SummaryRequest):
    try:
        # Validar que se proporcione al menos una URL o una transcripción
        if not request.url and not request.transcription:
            raise ValueError("Debe proporcionar una URL de video o una transcripción")
            
        result = await generate_summary(
            video_url=request.url,
            transcription=request.transcription,
            language_code=request.language_code,
            max_length=request.max_length
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Capturar y mostrar el error completo para depuración
        error_detail = f"Failed to summarize content: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)  # Logging para el servidor
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/youtube/auto", response_model=TranscriptionAndSummaryResponse)
async def transcribe_and_summarize(request: TranscriptionAndSummaryRequest):
    try:
        # Validar la URL
        if not request.url:
            raise ValueError("Debe proporcionar una URL de video")
        
        # Obtener el ID del video
        video_id = get_video_id(request.url)
        
        # Obtener la transcripción
        transcription = await get_video_transcript(
            video_url=request.url,
            language_code=request.language_code
        )
        
        if not transcription:
            raise ValueError("No se pudo obtener la transcripción del video")
        
        # Generar el resumen automáticamente
        result = await generate_summary(
            transcription=transcription,
            language_code=request.language_code,
            max_length=request.max_length
        )
        
        # Devolver tanto la transcripción como el resumen
        return {
            "transcription": transcription,
            "summary": result["summary"],
            "video_id": video_id,
            "video_url": request.url
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Capturar y mostrar el error completo para depuración
        error_detail = f"Failed to transcribe and summarize: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)  # Logging para el servidor
        raise HTTPException(status_code=500, detail=str(e)) 