from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Union
import uuid, time
from agent.agent import generate_response
from services.memory import memory_service
from config import settings

router = APIRouter()

class ResponseRequest(BaseModel):
    model: str = settings.model_name
    input: Union[str, List[dict]]
    session_id: Optional[str] = None

def verify_token(request: Request):
    if settings.auth_token:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid token")
        token = auth_header.split(" ")[1]
        if token != settings.auth_token:
            raise HTTPException(status_code=403, detail="Invalid token")
    return True

@router.post("/responses")
async def create_response(payload: ResponseRequest, request: Request, _=Depends(verify_token)):
    try:
        # 1. Extraer entrada
        if isinstance(payload.input, str):
            user_input = payload.input
        else:
            user_messages = [m for m in payload.input if m.get("role") == "user"]
            if not user_messages:
                raise HTTPException(status_code=400, detail="No user message found")
            user_input = user_messages[-1]["content"]

        # 2. Obtener o generar session_id
        session_id = payload.session_id or str(uuid.uuid4())

        # 3. Cargar historial
        history = memory_service.load_history(session_id)

        # 4. Construir prompt con historial (si hay)
        if history:
            history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in history])
            prompt_for_agent = f"Historial de conversación:\n{history_text}\n\nNueva pregunta: {user_input}"
        else:
            prompt_for_agent = user_input

        # 5. Generar respuesta (async)
        response_text = await generate_response(prompt_for_agent, session_id)

        # 6. Guardar mensajes en historial
        memory_service.save_message(session_id, {"role": "user", "content": user_input})
        memory_service.save_message(session_id, {"role": "assistant", "content": response_text})

        # 7. Construir respuesta en formato OpenAI Responses
        response = {
            "id": f"resp_{uuid.uuid4().hex[:24]}",
            "object": "response",
            "created_at": int(time.time()),
            "model": payload.model,
            "output": [
                {
                    "type": "message",
                    "role": "assistant",
                    "content": [{"type": "output_text", "text": response_text}],
                }
            ],
            "usage": {
                "input_tokens": len(user_input.split()),
                "output_tokens": len(response_text.split()),
            },
        }
        return response
    except Exception as e:
        print(f"Error en responses: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))