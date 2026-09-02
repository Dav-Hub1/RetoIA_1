import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from endpoints import agent_card, responses
from services.supabase_client import supabase_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    supabase_service.connect()
    yield
    # Shutdown (opcional)
    # Aquí puedes cerrar conexiones si es necesario

app = FastAPI(title="Manager", lifespan=lifespan)

app.include_router(agent_card.router)
app.include_router(responses.router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)