from pydantic import BaseModel
from typing import Optional

class SummaryRequest(BaseModel):
    url: Optional[str] = None
    transcription: Optional[str] = None
    language_code: Optional[str] = "es"
    max_length: Optional[int] = 500

class SummaryResponse(BaseModel):
    summary: str
    video_id: Optional[str] = None
    video_url: Optional[str] = None 