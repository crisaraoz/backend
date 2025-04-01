from pydantic import BaseModel
from typing import Optional

class TranscriptionRequest(BaseModel):
    video_url: str
    language_code: Optional[str] = "en"  # Default to English, but can be overridden
    transcription_type: Optional[str] = None  # 'generated' or 'manual' or None (for any)
    use_generated: Optional[bool] = False  # Whether to use generated transcripts

class TranscriptionResponse(BaseModel):
    transcription: str 