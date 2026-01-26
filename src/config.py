"""Configuration management for the application."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # PostgreSQL Configuration
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str
    postgres_password: str
    postgres_db: str
    
    # Groq API
    groq_api_key: str = "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"
    groq_model: str = "llama-3.3-70b-versatile"
    
    # Application Settings
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = False
    
    # MCP Server (runs in separate container)
    mcp_server_command: str = "docker"
    mcp_server_args: str = "exec,-i,query-agent-mcp-server,npx,@modelcontextprotocol/server-postgres"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @property
    def postgres_url(self) -> str:
        """Construct PostgreSQL connection URL."""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )
    
    @property
    def mcp_args_list(self) -> list[str]:
        """Parse MCP server arguments into a list."""
        return self.mcp_server_args.split(',')


# Global settings instance
settings = Settings()
