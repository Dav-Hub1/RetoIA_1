import requests
from typing import Any, cast, Optional
from config import settings
from services.supabase_client import supabase_service

class RAGService:
    def __init__(self):
        # Usar el cliente admin (service_role) para evitar RLS
        self.supabase = supabase_service.connect_admin()
        self.embedding_url = "https://api.mistral.ai/v1/embeddings"
        self.headers = {
            "Authorization": f"Bearer {settings.mistral_api_key}",
            "Content-Type": "application/json"
        }

    def _get_embedding(self, text: str) -> list[float]:
        """Genera el embedding de la consulta usando Mistral."""
        payload = {
            "input": text,
            "model": settings.embedding_model
        }
        try:
            response = requests.post(self.embedding_url, json=payload, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            embedding = data["data"][0]["embedding"]
            # Asegurar que sea lista de floats
            return [float(x) for x in embedding]
        except Exception as e:
            print(f"Error generating embedding: {e}")
            raise

    def retrieve(self, query: str, top_k: Optional[int] = None, filter_: Optional[dict[str, Any]] = None) -> list[dict[str, Any]]:
        """
        Recupera los chunks más similares desde Supabase.
        """
        top_k = top_k or settings.top_k_retrieval
        filter_ = filter_ or {}

        # 1. Obtener embedding de la consulta
        query_embedding = self._get_embedding(query)

        # 2. Llamar a la función RPC match_cv_analytics
        try:
            # Asegurar que el embedding sea una lista de floats
            result = self.supabase.rpc(
                settings.match_function,
                {
                    "query_embedding": query_embedding,
                    "match_count": top_k,
                    "filter": filter_
                }
            ).execute()
            
            if result.data:
                return cast(list[dict[str, Any]], result.data)
            return []
        except Exception as e:
            print(f"Error in RPC: {e}")
            import traceback
            traceback.print_exc()
            return []

    def format_context(self, retrieved_chunks: list[dict[str, Any]]) -> str:
        """Concatena los contenidos recuperados en un solo string."""
        if not retrieved_chunks:
            return ""
        parts = []
        for i, chunk in enumerate(retrieved_chunks):
            if 'content' in chunk:
                parts.append(f"[Contexto {i+1}]\n{chunk['content']}")
        return "\n\n".join(parts)

rag_service = RAGService()