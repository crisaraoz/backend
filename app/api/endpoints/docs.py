from fastapi import APIRouter, HTTPException
from app.schemas.docs import DocProcessRequest, DocProcessResponse, DocQueryRequest, DocQueryResponse
from app.services.docs import process_documentation, query_documentation
import traceback

router = APIRouter()

@router.post("/process", response_model=DocProcessResponse)
async def process_doc(request: DocProcessRequest):
    """
    Procesa una URL de documentación y genera un resumen con conceptos clave.
    """
    try:
        if not request.url:
            raise ValueError("Debe proporcionar una URL de documentación")
            
        result = await process_documentation(
            url=request.url,
            language_code=request.language_code,
            max_length=request.max_length
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        error_detail = f"Failed to process documentation: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)  # Logging para el servidor
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query", response_model=DocQueryResponse)
async def query_doc(request: DocQueryRequest):
    """
    Realiza una consulta sobre la documentación procesada.
    """
    try:
        if not request.doc_id or not request.query:
            raise ValueError("Debe proporcionar un ID de documento y una consulta")
            
        result = await query_documentation(
            doc_id=request.doc_id,
            query=request.query,
            language_code=request.language_code
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        error_detail = f"Failed to query documentation: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)  # Logging para el servidor
        raise HTTPException(status_code=500, detail=str(e)) 