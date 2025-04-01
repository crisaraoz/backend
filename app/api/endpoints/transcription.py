from fastapi import APIRouter, HTTPException
from app.schemas.transcription import TranscriptionRequest, TranscriptionResponse
from app.services.transcription import get_video_transcript
import traceback

router = APIRouter()

@router.post("/youtube", response_model=TranscriptionResponse)
async def transcribe_youtube_video(request: TranscriptionRequest):
    try:
        transcription = await get_video_transcript(
            request.video_url,
            language_code=request.language_code,
            transcription_type=request.transcription_type,
            use_generated=request.use_generated
        )
        return {"transcription": transcription}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Capturar y mostrar el error completo para depuración
        error_detail = f"Failed to process video: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)  # Logging para el servidor
        raise HTTPException(status_code=500, detail=str(e)) 