from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.api.chat.service import generate_chat_response

router = APIRouter()

class Message(BaseModel):
    role: str  # "system", "user", or "assistant"
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    model: Optional[str] = "gpt-3.5-turbo"

@router.post("/chat")
async def chat_with_ai(request: ChatRequest):
    """
    Endpoint to chat with OpenAI model
    """
    if not request.messages:
        raise HTTPException(status_code=400, detail="No messages provided")
    
    # Convert Pydantic models to dictionaries for OpenAI
    formatted_messages = [
        {"role": msg.role, "content": msg.content} 
        for msg in request.messages
    ]
    
    response = await generate_chat_response(formatted_messages, request.model)
    
    if response["status"] == "error":
        raise HTTPException(status_code=500, detail=response["message"])
        
    return response
