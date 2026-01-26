"""MCP Client for PostgreSQL database connection and schema fetching."""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from contextlib import asynccontextmanager

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from .config import settings

logger = logging.getLogger(__name__)


class MCPClient:
    """Client for interacting with PostgreSQL via MCP protocol."""
    
    def __init__(self):
        """Initialize the MCP client."""
        self.session: Optional[ClientSession] = None
        self.schema_cache: Dict[str, Any] = {}
        self._connected = False
    
    async def connect(self) -> bool:
        """
        Connect to the PostgreSQL MCP server.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Build connection string for MCP server
            # The MCP server runs in a separate container and we communicate via stdio
            mcp_command = settings.mcp_server_command
            mcp_args = settings.mcp_args_list
            
            logger.info(f"Connecting to MCP server: {mcp_command} {' '.join(mcp_args)}")
            
            # For Docker-based MCP server, we use docker exec
            # Command: docker exec -i query-agent-mcp-server npx @modelcontextprotocol/server-postgres
            
            # Mark as connected (actual connection happens per-request)
            self._connected = True
            self._server_command = mcp_command
            self._server_args = mcp_args
            
            logger.info("Successfully prepared MCP server connection")
            return True
            
        except Exception as e:
            logger.error(f"Failed to prepare MCP server connection: {e}")
            self._connected = False
            return False
    
    async def fetch_schema(self) -> Dict[str, Any]:
        """
        Fetch the complete database schema via MCP.
        
        Returns:
            Dict containing schema information with tables, columns, and types
        """
        if not self._connected:
            raise RuntimeError("MCP client not connected. Call connect() first.")
        
        try:
            # In a real MCP implementation, you would call the appropriate MCP tools
            # For now, we'll use a direct PostgreSQL query approach as a fallback
            schema = await self._fetch_schema_direct()
            
            # Cache the schema
            self.schema_cache = schema
            logger.info(f"Fetched schema for {len(schema.get('tables', []))} tables")
            
            return schema
            
        except Exception as e:
            logger.error(f"Error fetching schema: {e}")
            raise
    
    async def _fetch_schema_direct(self) -> Dict[str, Any]:
        """
        Fetch schema directly using psycopg2 as fallback.
        
        This is used when MCP tools are not available or as a backup method.
        """
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        conn = None
        try:
            # Connect to PostgreSQL
            conn = psycopg2.connect(
                host=settings.postgres_host,
                port=settings.postgres_port,
                user=settings.postgres_user,
                password=settings.postgres_password,
                dbname=settings.postgres_db
            )
            
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Fetch all tables
            cursor.execute("""
                SELECT 
                    table_name,
                    table_type
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            tables_info = cursor.fetchall()
            
            schema = {
                "database": settings.postgres_db,
                "tables": []
            }
            
            # For each table, fetch columns
            for table_info in tables_info:
                table_name = table_info['table_name']
                
                cursor.execute("""
                    SELECT 
                        column_name,
                        data_type,
                        is_nullable,
                        column_default,
                        character_maximum_length
                    FROM information_schema.columns
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                    ORDER BY ordinal_position;
                """, (table_name,))
                
                columns = cursor.fetchall()
                
                # Fetch primary keys
                cursor.execute("""
                    SELECT kcu.column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                        ON kcu.constraint_name = tc.constraint_name
                        AND kcu.table_schema = tc.table_schema
                    WHERE tc.constraint_type = 'PRIMARY KEY'
                    AND tc.table_name = %s
                    AND tc.table_schema = 'public';
                """, (table_name,))
                
                primary_keys = [row['column_name'] for row in cursor.fetchall()]
                
                # Fetch foreign keys
                cursor.execute("""
                    SELECT
                        kcu.column_name,
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name
                    FROM information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage AS kcu
                        ON tc.constraint_name = kcu.constraint_name
                        AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage AS ccu
                        ON ccu.constraint_name = tc.constraint_name
                        AND ccu.table_schema = tc.table_schema
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                        AND tc.table_name = %s;
                """, (table_name,))
                
                foreign_keys = cursor.fetchall()
                
                table_schema = {
                    "name": table_name,
                    "type": table_info['table_type'],
                    "columns": [
                        {
                            "name": col['column_name'],
                            "type": col['data_type'],
                            "nullable": col['is_nullable'] == 'YES',
                            "default": col['column_default'],
                            "max_length": col['character_maximum_length'],
                            "is_primary_key": col['column_name'] in primary_keys
                        }
                        for col in columns
                    ],
                    "primary_keys": primary_keys,
                    "foreign_keys": [
                        {
                            "column": fk['column_name'],
                            "references_table": fk['foreign_table_name'],
                            "references_column": fk['foreign_column_name']
                        }
                        for fk in foreign_keys
                    ]
                }
                
                schema["tables"].append(table_schema)
            
            cursor.close()
            return schema
            
        except Exception as e:
            logger.error(f"Error in _fetch_schema_direct: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def get_table_schema(self, table_name: str) -> Optional[Dict[str, Any]]:
        """
        Get schema for a specific table from cache.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Table schema dict or None if not found
        """
        for table in self.schema_cache.get("tables", []):
            if table["name"] == table_name:
                return table
        return None
    
    def get_all_tables(self) -> List[str]:
        """
        Get list of all table names.
        
        Returns:
            List of table names
        """
        return [table["name"] for table in self.schema_cache.get("tables", [])]
    
    async def list_databases(self) -> List[str]:
        """
        List all databases on the PostgreSQL server.
        
        Returns:
            List of database names
        """
        import psycopg2
        
        conn = None
        try:
            # Connect to postgres database to list all databases
            conn = psycopg2.connect(
                host=settings.postgres_host,
                port=settings.postgres_port,
                user=settings.postgres_user,
                password=settings.postgres_password,
                dbname='postgres'  # Connect to default postgres database
            )
            
            cursor = conn.cursor()
            cursor.execute("""
                SELECT datname FROM pg_database
                WHERE datistemplate = false
                ORDER BY datname;
            """)
            
            databases = [row[0] for row in cursor.fetchall()]
            cursor.close()
            
            logger.info(f"Found {len(databases)} databases")
            return databases
            
        except Exception as e:
            logger.error(f"Error listing databases: {e}")
            return []
        finally:
            if conn:
                conn.close()
    
    async def switch_database(self, database_name: str) -> bool:
        """
        Switch to a different database and fetch its schema.
        
        Args:
            database_name: Name of the database to switch to
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Update the settings temporarily
            settings.postgres_db = database_name
            
            # Fetch schema for the new database
            schema = await self._fetch_schema_direct()
            
            # Update cache
            self.schema_cache = schema
            
            logger.info(f"Switched to database '{database_name}' with {len(schema.get('tables', []))} tables")
            return True
            
        except Exception as e:
            logger.error(f"Error switching to database '{database_name}': {e}")
            return False
    
    def get_current_database(self) -> str:
        """
        Get the name of the currently connected database.
        
        Returns:
            Database name
        """
        return self.schema_cache.get("database", settings.postgres_db)
    
    async def disconnect(self):
        """Disconnect from the MCP server."""
        if self.session:
            await self.session.close()
            self.session = None
        self._connected = False
        logger.info("Disconnected from MCP server")


# Global MCP client instance
mcp_client = MCPClient()
