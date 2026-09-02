from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Union, Dict, Any
import uuid, time, json
from agent.agent import generate_response
from services.memory import memory_service
from config import settings

router = APIRouter()

class MessageContent(BaseModel):
    type: str = "text"
    text: Optional[str] = None
    image_url: Optional[Dict[str, Any]] = None

class Message(BaseModel):
    type: str = "message"
    role: str  # "user", "assistant", "system"
    content: Union[str, List[MessageContent]]

class ResponseRequest(BaseModel):
    model: str = settings.model_name
    input: Union[str, List[Message]]
    session_id: Optional[str] = None
    instructions: Optional[str] = None

def verify_token(request: Request):
    if settings.auth_token:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(status_code=401, detail="Missing Authorization header")
        
        # Handle both "Bearer token" and "token"
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
        else:
            token = auth_header
        
    return True

@router.post("/responses")
async def create_response(payload: ResponseRequest, request: Request, _=Depends(verify_token)):
    # 1. Extract user input
    if isinstance(payload.input, str):
        user_input = payload.input
        system_instructions = None
    else:
        # Process message list
        user_messages = []
        system_instructions = None
        
        for msg in payload.input:
            if msg.role == "user":
                if isinstance(msg.content, str):
                    user_messages.append(msg.content)
                else:
                    # Extract text from content list
                    text_parts = [c.text for c in msg.content if c.type == "text" and c.text]
                    user_messages.append(" ".join(text_parts))
            elif msg.role == "system":
                if isinstance(msg.content, str):
                    system_instructions = msg.content
                else:
                    text_parts = [c.text for c in msg.content if c.type == "text" and c.text]
                    system_instructions = " ".join(text_parts)
        
        if not user_messages:
            raise HTTPException(status_code=400, detail="No user message found")
        
        user_input = user_messages[-1]  # Last user message
    
    # 2. Get or generate session_id
    session_id = payload.session_id or str(uuid.uuid4())
    
    # 3. Load history
    history = memory_service.load_history(session_id)
    
    # 4. Build prompt with history
    if history:
        history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in history])
        prompt_for_agent = f"Conversation history:\n{history_text}\n\nNew question: {user_input}"
    else:
        prompt_for_agent = user_input
    
    # Add system instructions if provided
    if system_instructions or payload.instructions:
        instructions = system_instructions or payload.instructions
        prompt_for_agent = f"Instructions: {instructions}\n\n{prompt_for_agent}"
    
    # 5. Generate response
    response_text = await generate_response(prompt_for_agent, session_id)
    
    # 6. Save messages
    memory_service.save_message(session_id, {"role": "user", "content": user_input})
    memory_service.save_message(session_id, {"role": "assistant", "content": response_text})
    
    # 7. Build ResponseResource schema
    response = {
        "id": f"resp_{uuid.uuid4().hex[:24]}",
        "object": "response",
        "created_at": int(time.time()),
        "model": payload.model,
        "output": [
            {
                "type": "message",
                "role": "assistant",
                "phase": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": response_text
                    }
                ]
            }
        ],
        "usage": {
            "input_tokens": len(prompt_for_agent.split()),
            "output_tokens": len(response_text.split()),
            "total_tokens": len(prompt_for_agent.split()) + len(response_text.split())
        }
    }
    
    return response