from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
import hashlib
import json

from app.models.docs import Documentation, DocumentationPage, SearchIndex

def create_documentation(db: Session, doc_data: Dict[str, Any]) -> Documentation:
    """
    Crea un nuevo registro de documentación en la base de datos.
    """
    doc_id = hashlib.md5(doc_data['url'].encode()).hexdigest()
    
    db_doc = Documentation(
        id=doc_id,
        url=doc_data['url'],
        title=doc_data['title'],
        summary=doc_data.get('summary', ''),
        key_concepts=json.dumps(doc_data.get('key_concepts', [])),
        processed_at=doc_data.get('processed_at'),
        status=doc_data.get('status', 'pending'),
        sections_analyzed=doc_data.get('sections_analyzed', 0),
        total_pages=doc_data.get('total_pages', 0),
        completion_percentage=doc_data.get('completion_percentage', 0.0),
        message=doc_data.get('message', ''),
        language_code=doc_data.get('language_code', 'es')
    )
    
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)
    return db_doc

def update_documentation_status(db: Session, doc_id: str, status_data: Dict[str, Any]) -> Optional[Documentation]:
    """
    Actualiza el estado de una documentación.
    """
    db_doc = db.query(Documentation).filter(Documentation.id == doc_id).first()
    if not db_doc:
        return None
        
    for key, value in status_data.items():
        if hasattr(db_doc, key):
            setattr(db_doc, key, value)
    
    db.commit()
    db.refresh(db_doc)
    return db_doc

def get_documentation(db: Session, doc_id: str) -> Optional[Documentation]:
    """
    Obtiene una documentación por su ID.
    """
    return db.query(Documentation).filter(Documentation.id == doc_id).first()

def get_documentation_by_url(db: Session, url: str) -> Optional[Documentation]:
    """
    Obtiene una documentación por su URL.
    """
    doc_id = hashlib.md5(url.encode()).hexdigest()
    return db.query(Documentation).filter(Documentation.id == doc_id).first()

def add_documentation_page(db: Session, doc_id: str, page_data: Dict[str, Any]) -> DocumentationPage:
    """
    Añade una página a una documentación.
    """
    page_id = hashlib.md5(page_data['url'].encode()).hexdigest()
    
    db_page = DocumentationPage(
        id=page_id,
        doc_id=doc_id,
        url=page_data['url'],
        title=page_data['title'],
        content=page_data.get('content', ''),
        processed_at=page_data.get('processed_at'),
        importance_score=page_data.get('importance_score', 1.0)
    )
    
    db.add(db_page)
    db.commit()
    db.refresh(db_page)
    return db_page

def get_documentation_pages(db: Session, doc_id: str) -> List[DocumentationPage]:
    """
    Obtiene todas las páginas de una documentación.
    """
    return db.query(DocumentationPage).filter(DocumentationPage.doc_id == doc_id).all()

def create_search_index(db: Session, doc_id: str, keyword: str, page_id: str, relevance: float = 1.0) -> SearchIndex:
    """
    Crea una entrada en el índice de búsqueda.
    """
    index_id = f"{doc_id}_{keyword}_{page_id}"
    
    db_index = SearchIndex(
        id=index_id,
        doc_id=doc_id,
        keyword=keyword,
        page_id=page_id,
        relevance=relevance
    )
    
    db.add(db_index)
    db.commit()
    db.refresh(db_index)
    return db_index

def search_documentation(db: Session, doc_id: str, query: str) -> List[Dict[str, Any]]:
    """
    Busca en una documentación usando el índice de búsqueda.
    """
    # Procesamiento básico de la consulta
    keywords = [word.lower() for word in query.split() if len(word) > 3]
    
    # Buscar páginas relevantes
    relevant_pages = {}
    
    for keyword in keywords:
        # Búsqueda con LIKE para simplicidad (en producción usaríamos búsqueda de texto completo o vectorial)
        results = db.query(SearchIndex).filter(
            SearchIndex.doc_id == doc_id,
            SearchIndex.keyword.like(f"%{keyword}%")
        ).all()
        
        for result in results:
            if result.page_id not in relevant_pages:
                relevant_pages[result.page_id] = 0
            relevant_pages[result.page_id] += result.relevance
    
    # Ordenar por relevancia
    page_ids = sorted(relevant_pages.keys(), key=lambda x: relevant_pages[x], reverse=True)
    
    # Obtener datos de las páginas
    pages = []
    for page_id in page_ids[:5]:  # Limitamos a las 5 páginas más relevantes
        page = db.query(DocumentationPage).filter(DocumentationPage.id == page_id).first()
        if page:
            pages.append({
                "id": page.id,
                "url": page.url,
                "title": page.title,
                "content": page.content[:1000] + "...",  # Extracto
                "relevance": relevant_pages[page_id]
            })
    
    return pages 