from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class DocProcessRequest(BaseModel):
    url: str
    language_code: Optional[str] = "es"
    max_length: Optional[int] = 1000
    analyze_subsections: Optional[bool] = True
    max_depth: Optional[int] = 3  # Profundidad máxima para analizar la documentación
    excluded_paths: Optional[List[str]] = []  # Patrones para excluir en el crawling

class DocProcessResponse(BaseModel):
    url: str
    title: str
    summary: str
    key_concepts: List[str]
    processed_at: str
    # Nuevos campos para el crawling
    sections_analyzed: int = 1
    total_pages: int = 1
    completion_percentage: float = 100.0
    message: Optional[str] = None
    status: str = "completed"

class DocStatusRequest(BaseModel):
    url: str

class DocStatusResponse(BaseModel):
    url: str
    status: str  # "in_progress", "completed", "failed"
    sections_analyzed: int
    total_pages: int
    completion_percentage: float
    message: Optional[str] = None

class DocQueryRequest(BaseModel):
    url: str  # Cambiado de doc_id a url para ser consistente con el frontend
    query: str
    language_code: Optional[str] = "es"
    max_tokens: Optional[int] = 2000
    include_sources: Optional[bool] = True

class DocQueryResponse(BaseModel):
    answer: str
    sources: List[str]  # Cambiado a "sources" para ser consistente con el frontend
    confidence: float 