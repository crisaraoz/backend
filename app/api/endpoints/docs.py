from fastapi import APIRouter, HTTPException, Query
from app.schemas.docs import (
    DocProcessRequest, DocProcessResponse, 
    DocQueryRequest, DocQueryResponse,
    DocStatusRequest, DocStatusResponse
)
from app.services.docs import process_documentation, query_documentation, get_documentation_status
import traceback

router = APIRouter()

@router.post("/process", response_model=DocProcessResponse)
async def process_doc(request: DocProcessRequest):
    """
    Procesa una URL de documentación, analiza su contenido y opcionalmente realiza crawling de subsecciones.
    
    - Extrae el contenido de la página principal
    - Si analyze_subsections=True, analiza también las páginas vinculadas
    - Genera un resumen con conceptos clave
    - Construye un índice para consultas posteriores
    """
    try:
        if not request.url:
            raise ValueError("Debe proporcionar una URL de documentación")
            
        result = await process_documentation(
            url=request.url,
            language_code=request.language_code,
            max_length=request.max_length,
            analyze_subsections=request.analyze_subsections,
            max_depth=request.max_depth,
            excluded_paths=request.excluded_paths
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        error_detail = f"Failed to process documentation: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)  # Logging para el servidor
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status", response_model=DocStatusResponse)
async def get_doc_status(url: str = Query(..., description="URL de la documentación procesada")):
    """
    Obtiene el estado actual del procesamiento de una documentación.
    Útil para monitorear el progreso del análisis de documentaciones grandes.
    """
    try:
        if not url:
            raise ValueError("Debe proporcionar una URL de documentación")
            
        result = await get_documentation_status(url=url)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        error_detail = f"Failed to get documentation status: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)  # Logging para el servidor
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query", response_model=DocQueryResponse)
async def query_doc(request: DocQueryRequest):
    """
    Realiza una consulta sobre la documentación procesada utilizando el índice construido.
    La documentación debe haber sido procesada previamente con /process.
    """
    try:
        if not request.url or not request.query:
            raise ValueError("Debe proporcionar una URL de documento y una consulta")
            
        result = await query_documentation(
            url=request.url,
            query=request.query,
            language_code=request.language_code,
            max_tokens=request.max_tokens,
            include_sources=request.include_sources
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        error_detail = f"Failed to query documentation: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)  # Logging para el servidor
        raise HTTPException(status_code=500, detail=str(e)) 