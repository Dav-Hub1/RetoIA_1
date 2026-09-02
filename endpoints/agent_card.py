from fastapi import APIRouter, Request
from config import settings

router = APIRouter()

@router.get("/.well-known/agent-card.json")
async def get_agent_card(request: Request):
    base_url = str(request.base_url).rstrip("/")

    return {
        "name": settings.agent_name,
        "description": settings.agent_description,
        "url": base_url,
        "provider": {
            "organization": "David de la Cruz",
            "url": base_url
        },
        "version": "1.0.0",
        "supportedInterfaces": [
            {
                "type": "responses",
                "url": f"{base_url}/responses",
                "specification": "openai-responses",
                "capabilities": {
                    "streaming": False,
                    "pushNotifications": False,
                    "stateful": True
                }
            }
        ],
        "authentication": {
            "type": "bearer",
            "scheme": "bearer",
            "description": "Use Authorization: Bearer <token>"
        } if settings.auth_token else None,
        "defaultInputModes": ["text"],
        "defaultOutputModes": ["text"],
        "endpoints": {
            "responses": "/responses"
        }
    }