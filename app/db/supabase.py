"""
Async Supabase database client.

Provides:
- Singleton async client initialization
- Query execution helpers with error handling
- Connection management for FastAPI lifespan
"""

from contextlib import asynccontextmanager
from typing import Any, Optional

from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions

from app.core.config import get_settings

# Global client instance
_supabase_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """
    Get the Supabase client singleton.
    
    Client is initialized on first call and reused thereafter.
    Uses service role key for full database access (RLS is enforced via policies).
    
    Returns:
        Configured Supabase client
        
    Raises:
        RuntimeError: If client initialization fails
    """
    global _supabase_client
    
    if _supabase_client is None:
        settings = get_settings()
        
        # Configure client options
        options = ClientOptions(
            postgrest_client_timeout=30,  # 30 second timeout
            storage_client_timeout=30,
        )
        
        _supabase_client = create_client(
            settings.supabase_url,
            settings.supabase_key,
            options=options
        )
    
    return _supabase_client


async def close_supabase_client() -> None:
    """
    Clean up Supabase client resources.
    
    Called during application shutdown.
    """
    global _supabase_client
    
    if _supabase_client is not None:
        # Supabase client doesn't have explicit close, but we clear reference
        _supabase_client = None


# ─────────────────────────────────────────────────────────────────────────────
# Query Helper Functions
# ─────────────────────────────────────────────────────────────────────────────

async def execute_query(
    table: str,
    query_builder: Any
) -> list[dict]:
    """
    Execute a Supabase query and return results.
    
    Args:
        table: Table name for error context
        query_builder: Configured query from client.table().select() etc.
        
    Returns:
        List of row dictionaries
        
    Raises:
        RuntimeError: If query execution fails
    """
    try:
        response = query_builder.execute()
        return response.data
    except Exception as e:
        raise RuntimeError(f"Query on {table} failed: {str(e)}")


async def insert_row(
    table: str,
    data: dict
) -> dict:
    """
    Insert a single row and return it.
    
    Args:
        table: Target table name
        data: Row data as dictionary
        
    Returns:
        Inserted row with generated fields (id, created_at, etc.)
        
    Raises:
        RuntimeError: If insert fails
    """
    client = get_supabase_client()
    
    try:
        response = client.table(table).insert(data).execute()
        if response.data:
            return response.data[0]
        raise RuntimeError(f"Insert into {table} returned no data")
    except Exception as e:
        raise RuntimeError(f"Insert into {table} failed: {str(e)}")


async def update_row(
    table: str,
    row_id: str,
    data: dict,
    id_column: str = "id"
) -> dict:
    """
    Update a single row by ID.
    
    Args:
        table: Target table name
        row_id: Row identifier value
        data: Fields to update
        id_column: Name of the ID column (default: "id")
        
    Returns:
        Updated row data
        
    Raises:
        RuntimeError: If update fails or row not found
    """
    client = get_supabase_client()
    
    try:
        response = (
            client.table(table)
            .update(data)
            .eq(id_column, row_id)
            .execute()
        )
        if response.data:
            return response.data[0]
        raise RuntimeError(f"Row {row_id} not found in {table}")
    except Exception as e:
        raise RuntimeError(f"Update on {table} failed: {str(e)}")


async def delete_row(
    table: str,
    row_id: str,
    id_column: str = "id"
) -> bool:
    """
    Delete a single row by ID.
    
    Args:
        table: Target table name
        row_id: Row identifier value
        id_column: Name of the ID column (default: "id")
        
    Returns:
        True if deleted successfully
        
    Raises:
        RuntimeError: If delete fails
    """
    client = get_supabase_client()
    
    try:
        response = (
            client.table(table)
            .delete()
            .eq(id_column, row_id)
            .execute()
        )
        return True
    except Exception as e:
        raise RuntimeError(f"Delete on {table} failed: {str(e)}")


async def fetch_one(
    table: str,
    row_id: str,
    columns: str = "*",
    id_column: str = "id"
) -> Optional[dict]:
    """
    Fetch a single row by ID.
    
    Args:
        table: Target table name
        row_id: Row identifier value
        columns: Columns to select (default: all)
        id_column: Name of the ID column (default: "id")
        
    Returns:
        Row data or None if not found
    """
    client = get_supabase_client()
    
    try:
        response = (
            client.table(table)
            .select(columns)
            .eq(id_column, row_id)
            .limit(1)
            .execute()
        )
        return response.data[0] if response.data else None
    except Exception as e:
        raise RuntimeError(f"Fetch from {table} failed: {str(e)}")


async def fetch_many(
    table: str,
    filters: Optional[dict] = None,
    columns: str = "*",
    order_by: Optional[str] = None,
    order_desc: bool = False,
    limit: Optional[int] = None,
    offset: Optional[int] = None
) -> list[dict]:
    """
    Fetch multiple rows with optional filters.
    
    Args:
        table: Target table name
        filters: Dict of column=value equality filters
        columns: Columns to select
        order_by: Column to order by
        order_desc: Order descending if True
        limit: Maximum rows to return
        offset: Number of rows to skip
        
    Returns:
        List of row dictionaries
    """
    client = get_supabase_client()
    
    try:
        query = client.table(table).select(columns)
        
        # Apply filters
        if filters:
            for col, val in filters.items():
                query = query.eq(col, val)
        
        # Apply ordering
        if order_by:
            query = query.order(order_by, desc=order_desc)
        
        # Apply pagination
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)
        
        response = query.execute()
        return response.data
    except Exception as e:
        raise RuntimeError(f"Fetch from {table} failed: {str(e)}")
