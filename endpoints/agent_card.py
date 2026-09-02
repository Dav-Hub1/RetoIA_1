from fastapi import APIRouter, Request
from config import settings

router = APIRouter()

@router.get("/.well-known/agent-card.json")
async def get_agent_card(request: Request):
    base_url = str(request.base_url).rstrip("/")

    # Build the response dictionary
    response = {
        "name": settings.agent_name,
        "description": settings.agent_description,
        "url": base_url,
        "version": "1.0.0",
        "supportedInterfaces": [
            {
                "type": "open-responses",           # ← indica claramente Open Responses
                "url": f"{base_url}/responses",
                "specification": "openai-responses"
            }
        ],
        "defaultInputModes": ["text"],
        "defaultOutputModes": ["text"]
    }

    if settings.auth_token:
        response["authentication"] = {
            "type": "bearer",
            "scheme": "bearer",
            "description": "Use Authorization: Bearer <token>"
        }

    return response