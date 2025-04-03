from pydantic import BaseModel
from typing import Optional, List

class DocProcessRequest(BaseModel):
    url: str
    language_code: Optional[str] = "es"
    max_length: Optional[int] = 1000

class DocProcessResponse(BaseModel):
    url: str
    title: str
    summary: str
    key_concepts: List[str]
    processed_at: str

class DocQueryRequest(BaseModel):
    doc_id: str
    query: str
    language_code: Optional[str] = "es"

class DocQueryResponse(BaseModel):
    answer: str
    relevant_sections: List[str]
    confidence: float 