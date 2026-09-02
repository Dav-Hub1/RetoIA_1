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
        "version": "1.0.0",
        "capabilities": {
            "responses": True,
            "streaming": False,
            "pushNotifications": False,
        },
        "authentication": {
            "type": "bearer" if settings.auth_token else "none",
        },
        "defaultInputModes": ["text"],
        "defaultOutputModes": ["text"],
        "endpoints": {
            "responses": "/responses",
        },
    }