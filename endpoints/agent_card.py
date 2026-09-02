from fastapi import APIRouter, Request
from config import settings

router = APIRouter()

@router.get("/.well-known/agent-card.json")
async def get_agent_card(request: Request):
    base_url = str(request.base_url).rstrip("/")

    # Build the response dictionary
    response = {
        "protocolVersion": "1.1.2",
        "name": settings.agent_name,
        "description": settings.agent_description,
        "url": base_url,
        "version": "1.0.0",
        "supportedInterfaces": [
            {
                "url": f"{base_url}/responses",
                "protocolBinding": "http",
                "protocolVersion": "open-responses"
            }
        ],
        "capabilities": {
            "streaming": False,
            "pushNotifications": False,
            "stateful": True
        },
        "defaultInputModes": ["text"],
        "defaultOutputModes": ["text"],
        "skills": []
    }
    
    # Only add authentication if token is configured
    if settings.auth_token:
        response["authentication"] = {
            "type": "bearer",
            "scheme": "bearer",
            "description": "Use Authorization: Bearer <token>"
        }
    
    return response