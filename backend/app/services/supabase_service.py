"""Supabase service for database operations."""

from typing import Dict, List, Optional, Any
from app.database import get_supabase

class SupabaseService:
    """Service class for Supabase operations."""
    
    @staticmethod
    def get_client():
        """Get Supabase client."""
        return get_supabase()
    
    @staticmethod
    def select(table: str, columns: str = "*", filters: Optional[Dict] = None) -> List[Dict]:
        """Select data from a table."""
        client = SupabaseService.get_client()
        query = client.table(table).select(columns)
        
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
        
        result = query.execute()
        return result.data
    
    @staticmethod
    def insert(table: str, data: Dict) -> Dict:
        """Insert data into a table."""
        client = SupabaseService.get_client()
        result = client.table(table).insert(data).execute()
        return result.data[0] if result.data else {}
    
    @staticmethod
    def update(table: str, data: Dict, filters: Dict) -> Dict:
        """Update data in a table."""
        client = SupabaseService.get_client()
        query = client.table(table).update(data)
        
        for key, value in filters.items():
            query = query.eq(key, value)
        
        result = query.execute()
        return result.data[0] if result.data else {}
    
    @staticmethod
    def delete(table: str, filters: Dict) -> bool:
        """Delete data from a table."""
        client = SupabaseService.get_client()
        query = client.table(table).delete()
        
        for key, value in filters.items():
            query = query.eq(key, value)
        
        result = query.execute()
        return len(result.data) > 0
