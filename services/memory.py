import json
from typing import Any, cast
from supabase import Client
from services.supabase_client import supabase_service

class MemoryService:
    def __init__(self):
        # Usar el cliente admin (service_role) para evitar RLS
        self.supabase: Client = supabase_service.connect_admin()

    def save_message(self, session_id: str, message: dict):
        payload = {
            "session_id": session_id,
            "message": json.dumps(message)
        }
        self.supabase.table("pydantic_ai_chat_history").insert(payload).execute()

    def load_history(self, session_id: str, limit: int = 6) -> list[dict[str, Any]]:
        result = self.supabase.table("pydantic_ai_chat_history") \
            .select("message") \
            .eq("session_id", session_id) \
            .order("created_at", desc=False) \
            .limit(limit) \
            .execute()
        rows = cast(list[dict[str, Any]], getattr(result, "data", []))
        if rows:
            return [json.loads(cast(dict[str, Any], row)["message"]) for row in rows]
        return []

    def delete_session(self, session_id: str):
        self.supabase.table("pydantic_ai_chat_history") \
            .delete() \
            .eq("session_id", session_id) \
            .execute()

memory_service = MemoryService()