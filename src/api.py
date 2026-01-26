"""FastAPI application for the PostgreSQL Query Generation Agent."""

import logging
from contextlib import asynccontextmanager
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

from .config import settings
from .mcp_client import mcp_client
from .schema_manager import SchemaManager
from .query_agent import QueryAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.debug else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Global instances
schema_manager: Optional[SchemaManager] = None
query_agent: Optional[QueryAgent] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown."""
    global schema_manager, query_agent
    
    # Startup
    logger.info("Starting up PostgreSQL Query Agent...")
    try:
        # Connect to database via MCP
        await mcp_client.connect()
        
        # Initialize schema manager
        schema_manager = SchemaManager(mcp_client)
        
        # Fetch initial schema
        await schema_manager.get_schema()
        
        # Initialize query agent
        query_agent = QueryAgent(schema_manager)
        
        logger.info("Application startup complete")
    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    await mcp_client.disconnect()


# Create FastAPI app
app = FastAPI(
    title="PostgreSQL Query Generation Agent",
    description="Generate SQL queries from natural language using AI",
    version="1.0.0",
    lifespan=lifespan
)


# Pydantic models for request/response
class QueryRequest(BaseModel):
    """Request model for query generation."""
    request: str
    conversation_history: Optional[List[dict]] = None


class QueryResponse(BaseModel):
    """Response model for generated queries."""
    query: Optional[str]
    explanation: str
    query_type: str
    tables_used: List[str]
    warnings: str
    is_safe: bool
    error: Optional[str] = None


class TableInfo(BaseModel):
    """Model for table information."""
    name: str
    columns: List[dict]
    primary_keys: List[str]
    foreign_keys: List[dict]


# API Endpoints

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main HTML page."""
    return FileResponse("static/index.html")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "database": settings.postgres_db,
        "tables_count": len(schema_manager.get_all_table_names()) if schema_manager else 0
    }


@app.get("/api/schema")
async def get_schema():
    """Get the complete database schema."""
    try:
        schema = await schema_manager.get_schema()
        return schema
    except Exception as e:
        logger.error(f"Error fetching schema: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/api/tables")
async def get_tables() -> List[str]:
    """Get list of all table names."""
    try:
        return schema_manager.get_all_table_names()
    except Exception as e:
        logger.error(f"Error fetching tables: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/databases")
async def get_databases() -> Dict[str, Any]:
    """Get list of all databases on the server."""
    try:
        databases = await mcp_client.list_databases()
        current_db = mcp_client.get_current_database()
        return {
            "databases": databases,
            "current": current_db,
            "count": len(databases)
        }
    except Exception as e:
        logger.error(f"Error fetching databases: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/switch-database")
async def switch_database(database: str) -> Dict[str, Any]:
    """
    Switch to a different database.
    
    Args:
        database: Name of the database to switch to
    """
    try:
        success = await mcp_client.switch_database(database)
        
        if success:
            # Refresh schema manager
            await schema_manager.get_schema(force_refresh=True)
            
            return {
                "status": "success",
                "database": database,
                "tables_count": len(schema_manager.get_all_table_names())
            }
        else:
            raise HTTPException(status_code=400, detail=f"Failed to switch to database '{database}'")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error switching database: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/table/{table_name}")
async def get_table(table_name: str) -> TableInfo:
    """Get detailed information about a specific table."""
    try:
        table_info = schema_manager.get_table_info(table_name)
        if not table_info:
            raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
        return table_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching table info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate-query")
async def generate_query(request: QueryRequest) -> QueryResponse:
    """
    Generate SQL query from natural language request.
    
    IMPORTANT: This endpoint only GENERATES queries. It does NOT execute them.
    """
    try:
        result = await query_agent.generate_query(
            user_request=request.request,
            conversation_history=request.conversation_history
        )
        
        return QueryResponse(
            query=result.get("query"),
            explanation=result.get("explanation", ""),
            query_type=result.get("query_type", "UNKNOWN"),
            tables_used=result.get("tables_used", []),
            warnings=result.get("warnings", ""),
            is_safe=result.get("is_safe", False),
            error=result.get("error")
        )
    except Exception as e:
        logger.error(f"Error generating query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/explain-query")
async def explain_query(query: str) -> dict:
    """Explain what a SQL query does."""
    try:
        explanation = await query_agent.explain_query(query)
        return {"explanation": explanation}
    except Exception as e:
        logger.error(f"Error explaining query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/refresh-schema")
async def refresh_schema():
    """Force a refresh of the database schema."""
    try:
        schema = await schema_manager.get_schema(force_refresh=True)
        return {
            "status": "success",
            "tables_count": len(schema.get("tables", []))
        }
    except Exception as e:
        logger.error(f"Error refreshing schema: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug
    )
