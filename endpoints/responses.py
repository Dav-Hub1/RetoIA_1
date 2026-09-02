from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Union, Any
import uuid, time
from agent.agent import generate_response
from services.memory import memory_service
from config import settings

router = APIRouter()

class ResponseRequest(BaseModel):
    model: str = settings.model_name
    input: Union[str, List[dict]]
    session_id: Optional[str] = None
    instructions: Optional[str] = None

def verify_token(request: Request):
    if not settings.auth_token:
        return True

    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    parts = auth_header.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        token = parts[1]
    elif len(parts) == 1:
        token = parts[0]
    else:
        raise HTTPException(status_code=401, detail="Invalid Authorization format")

    # Comparar directamente con settings.auth_token (que es str)
    if token != settings.auth_token:
        raise HTTPException(status_code=403, detail="Invalid token")

    return True

def extract_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        texts = []
        for item in content:
            if isinstance(item, str):
                texts.append(item)
            elif isinstance(item, dict):
                if item.get("type") == "text" and item.get("text"):
                    texts.append(item["text"])
                elif item.get("text"):
                    texts.append(item["text"])
        return " ".join(texts)
    return str(content)

@router.post("/responses")
async def create_response(payload: ResponseRequest, request: Request, _=Depends(verify_token)):
    try:
        # 1. Extraer entrada
        if isinstance(payload.input, str):
            user_input = payload.input
        else:
            user_messages = []
            for m in payload.input:
                if isinstance(m, dict) and m.get("role") == "user":
                    content = m.get("content", "")
                    user_messages.append(extract_text(content))
            if not user_messages:
                raise HTTPException(status_code=400, detail="No user message found")
            user_input = user_messages[-1]

        # Asegurar string
        if not isinstance(user_input, str):
            user_input = str(user_input)

        # 2. Session
        session_id = payload.session_id or str(uuid.uuid4())

        # 3. Historial
        history = memory_service.load_history(session_id)

        # 4. Prompt
        if history:
            history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in history])
            prompt_for_agent = f"Historial de conversación:\n{history_text}\n\nNueva pregunta: {user_input}"
        else:
            prompt_for_agent = user_input

        if payload.instructions:
            prompt_for_agent = f"Instructions: {payload.instructions}\n\n{prompt_for_agent}"

        # 5. Generar respuesta
        response_text = await generate_response(prompt_for_agent, session_id)
        if not isinstance(response_text, str):
            response_text = str(response_text)

        # 6. Guardar
        memory_service.save_message(session_id, {"role": "user", "content": user_input})
        memory_service.save_message(session_id, {"role": "assistant", "content": response_text})

        # 7. Respuesta en formato OpenAI Responses
        response = {
            "id": f"resp_{uuid.uuid4().hex[:24]}",
            "object": "response",
            "created_at": int(time.time()),
            "status": "completed",
            "model": payload.model,
            "output": [
                {
                    "type": "message",
                    "role": "assistant",
                    "content": [
                        {
                            "type": "output_text",   # ← compatible con OpenAI Responses
                            "text": response_text
                        }
                    ]
                }
            ],
            "usage": {
                "input_tokens": len(user_input.split()),
                "output_tokens": len(response_text.split()),
                "total_tokens": len(user_input.split()) + len(response_text.split())
            }
        }
        return response

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error en responses: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))