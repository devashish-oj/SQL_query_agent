"""Schema manager for caching and formatting database schema."""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SchemaManager:
    """Manages database schema caching and formatting."""
    
    def __init__(self, mcp_client):
        """
        Initialize schema manager.
        
        Args:
            mcp_client: Instance of MCPClient
        """
        self.mcp_client = mcp_client
        self.last_refresh: Optional[datetime] = None
        self.refresh_interval = timedelta(minutes=5)
    
    async def get_schema(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get database schema, refreshing if necessary.
        
        Args:
            force_refresh: Force a schema refresh even if cache is valid
            
        Returns:
            Database schema dictionary
        """
        should_refresh = (
            force_refresh or
            self.last_refresh is None or
            datetime.now() - self.last_refresh > self.refresh_interval
        )
        
        if should_refresh:
            logger.info("Refreshing database schema...")
            schema = await self.mcp_client.fetch_schema()
            self.last_refresh = datetime.now()
            return schema
        
        return self.mcp_client.schema_cache
    
    def format_schema_for_llm(self, table_names: Optional[List[str]] = None) -> str:
        """
        Format schema as a string for LLM context.
        
        Args:
            table_names: Optional list of specific tables to include.
                        If None, includes all tables.
        
        Returns:
            Formatted schema string
        """
        schema = self.mcp_client.schema_cache
        
        if not schema or "tables" not in schema:
            return "No schema information available."
        
        lines = [f"Database: {schema.get('database', 'Unknown')}\n"]
        tables = schema["tables"]
        
        # Filter tables if specific ones requested
        if table_names:
            tables = [t for t in tables if t["name"] in table_names]
        
        for table in tables:
            lines.append(f"\nTable: {table['name']}")
            lines.append("-" * 50)
            
            # Columns
            lines.append("Columns:")
            for col in table["columns"]:
                pk_marker = " (PRIMARY KEY)" if col.get("is_primary_key") else ""
                null_marker = "NULL" if col.get("nullable") else "NOT NULL"
                default = f" DEFAULT {col.get('default')}" if col.get("default") else ""
                
                lines.append(
                    f"  - {col['name']}: {col['type']} {null_marker}{default}{pk_marker}"
                )
            
            # Foreign keys
            if table.get("foreign_keys"):
                lines.append("\nForeign Keys:")
                for fk in table["foreign_keys"]:
                    lines.append(
                        f"  - {fk['column']} -> {fk['references_table']}.{fk['references_column']}"
                    )
        
        return "\n".join(lines)
    
    def get_table_info(self, table_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Table information dict or None if not found
        """
        return self.mcp_client.get_table_schema(table_name)
    
    def get_all_table_names(self) -> List[str]:
        """
        Get list of all table names in the database.
        
        Returns:
            List of table names
        """
        return self.mcp_client.get_all_tables()
    
    def format_schema_as_json(self) -> str:
        """
        Format schema as pretty-printed JSON.
        
        Returns:
            JSON string of schema
        """
        return json.dumps(self.mcp_client.schema_cache, indent=2)
    
    def get_column_names(self, table_name: str) -> List[str]:
        """
        Get list of column names for a specific table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            List of column names
        """
        table = self.get_table_info(table_name)
        if table:
            return [col["name"] for col in table["columns"]]
        return []
    
    def get_primary_keys(self, table_name: str) -> List[str]:
        """
        Get primary key columns for a table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            List of primary key column names
        """
        table = self.get_table_info(table_name)
        if table:
            return table.get("primary_keys", [])
        return []
