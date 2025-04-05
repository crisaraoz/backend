from sqlalchemy import Column, String, Text, Integer, Float, DateTime, Boolean, ForeignKey, JSON, func, LargeBinary
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY

from app.models.base import Base

class Documentation(Base):
    """Modelo para almacenar documentación procesada."""
    __tablename__ = "documentations"

    id = Column(String, primary_key=True)
    url = Column(String, index=True, nullable=False)
    title = Column(String, nullable=False)
    summary = Column(Text)
    key_concepts = Column(JSON)  # Lista de conceptos clave
    processed_at = Column(DateTime, default=func.now())
    status = Column(String, default="pending")  # pending, in_progress, completed, failed
    sections_analyzed = Column(Integer, default=0)
    total_pages = Column(Integer, default=0)
    completion_percentage = Column(Float, default=0.0)
    message = Column(Text)
    language_code = Column(String, default="es")
    # Nuevo campo para almacenar el embedding del resumen
    summary_embedding = Column(LargeBinary, nullable=True)

class DocumentationPage(Base):
    """Modelo para almacenar páginas individuales de una documentación."""
    __tablename__ = "documentation_pages"

    id = Column(String, primary_key=True)
    doc_id = Column(String, ForeignKey("documentations.id"), index=True)
    url = Column(String, index=True, nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text)
    processed_at = Column(DateTime, default=func.now())
    importance_score = Column(Float, default=1.0)  # Puntuación de importancia para búsquedas
    # Nuevo campo para almacenar el embedding del contenido
    content_embedding = Column(LargeBinary, nullable=True)
    # Almacenamos embeddings de cada párrafo para búsquedas más precisas
    paragraph_embeddings = Column(JSON, nullable=True)  # JSON que contiene {párrafo: embedding_bytes}

    # Relación con la documentación principal
    documentation = relationship("Documentation", back_populates="pages")

# Añadir relación inversa
Documentation.pages = relationship("DocumentationPage", back_populates="documentation")

class DocumentationChunk(Base):
    """
    Modelo para almacenar trozos de texto con sus embeddings.
    Esto permite búsquedas más granulares en documentos grandes.
    """
    __tablename__ = "documentation_chunks"

    id = Column(String, primary_key=True)
    doc_id = Column(String, ForeignKey("documentations.id"), index=True)
    page_id = Column(String, ForeignKey("documentation_pages.id"), index=True)
    content = Column(Text, nullable=False)  # El trozo de texto
    embedding = Column(LargeBinary, nullable=True)  # Vector de embedding serializado
    chunk_index = Column(Integer)  # Índice para ordenar los trozos
    
    # Relaciones
    documentation = relationship("Documentation")
    page = relationship("DocumentationPage")

class SearchIndex(Base):
    """Modelo para almacenar el índice de búsqueda para la documentación."""
    __tablename__ = "search_indices"

    id = Column(String, primary_key=True)
    doc_id = Column(String, ForeignKey("documentations.id"), index=True)
    keyword = Column(String, index=True)
    page_id = Column(String, ForeignKey("documentation_pages.id"))
    relevance = Column(Float, default=1.0)

    # Relaciones
    documentation = relationship("Documentation")
    page = relationship("DocumentationPage") 