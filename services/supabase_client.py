from typing import Optional
from supabase import create_client, Client
from config import settings

class SupabaseService:
    def __init__(self):
        self.url = settings.supabase_url
        self.key = settings.supabase_key
        self.service_key = settings.supabase_service_key
        self.client: Optional[Client] = None
        self.admin_client: Optional[Client] = None

    def connect(self) -> Client:
        """Cliente normal (anon key)"""
        if not self.client:
            self.client = create_client(self.url, self.key)
        return self.client

    def connect_admin(self) -> Client:
        """Cliente admin (service_role key) - omite RLS"""
        if not self.admin_client:
            self.admin_client = create_client(self.url, self.service_key)
        return self.admin_client

supabase_service = SupabaseService()