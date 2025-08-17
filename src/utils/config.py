"""
Configuration management for Idea Hub MCP Server

This module handles all configuration settings for the MCP server,
including database connections, AI service configurations, and server settings.
"""

import os
from dataclasses import dataclass
from typing import Optional
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    host: str = "localhost"
    port: int = 5432
    database: str = "idea_hub"
    username: str = "postgres"
    password: str = "password"
    
    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Create database config from environment variables."""
        return cls(
            host=os.getenv("DATABASE_HOST", "localhost"),
            port=int(os.getenv("DATABASE_PORT", "5432")),
            database=os.getenv("DATABASE_NAME", "idea_hub_db"),
            username=os.getenv("DATABASE_USER", "idea_user"),
            password=os.getenv("DATABASE_PASSWORD", "secure_idea_pass")
        )
    
    @property
    def connection_string(self) -> str:
        """Get PostgreSQL connection string."""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class AIConfig:
    """AI service configuration settings."""
    google_api_key: Optional[str] = None
    embedding_model: str = "all-MiniLM-L6-v2"  # Static - matches your existing setup
    llm_model: str = "gemini-2.5-flash"  # Static - matches your existing setup
    max_tokens: int = 4096  # Static
    temperature: float = 0.7  # Static
    
    @classmethod
    def from_env(cls) -> "AIConfig":
        """Create AI config from environment variables."""
        return cls(
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            # All other values are static - no environment overrides needed
            embedding_model="all-MiniLM-L6-v2",
            llm_model="gemini-2.5-flash",
            max_tokens=4096,
            temperature=0.7
        )


@dataclass
class ServerConfig:
    """MCP server configuration settings."""
    host: str = "localhost"  # Static
    port: int = 8000  # Static
    log_level: str = "INFO"  # Static
    debug: bool = False  # Static for production
    
    @classmethod
    def from_env(cls) -> "ServerConfig":
        """Create server config from environment variables."""
        return cls(
            # All values are static - no environment overrides needed
            host="localhost",
            port=8000,
            log_level="INFO",
            debug=False
        )


@dataclass
class VectorConfig:
    """Vector database configuration settings."""
    dimension: int = 384  # Static - for all-MiniLM-L6-v2
    similarity_threshold: float = 0.7  # Static - matches your existing Idea Hub
    max_results: int = 10  # Static
    duplicate_threshold: float = 0.8  # Static - matches your existing Idea Hub
    collaboration_threshold: float = 0.7  # Static - matches your existing Idea Hub
    
    @classmethod
    def from_env(cls) -> "VectorConfig":
        """Create vector config from environment variables."""
        return cls(
            # All values are static - matches your existing Idea Hub configuration
            dimension=384,
            similarity_threshold=0.7,
            max_results=10,
            duplicate_threshold=0.8,
            collaboration_threshold=0.7
        )


class MCPConfig:
    """Main configuration class for the MCP server."""
    
    def __init__(self):
        """Initialize configuration from environment variables."""
        self.database = DatabaseConfig.from_env()
        self.ai = AIConfig.from_env()
        self.server = ServerConfig.from_env()
        self.vector = VectorConfig.from_env()
        
        # Validate configuration
        self._validate()
    
    def _validate(self):
        """Validate configuration settings."""
        errors = []
        
        # Check required AI API key
        if not self.ai.google_api_key:
            errors.append("GOOGLE_API_KEY is required for AI features")
        
        # Check database connection info
        if not all([self.database.host, self.database.database, 
                   self.database.username, self.database.password]):
            errors.append("Database configuration incomplete - all DATABASE_* environment variables required")
        
        # Check vector dimension
        if self.vector.dimension <= 0:
            errors.append("Vector dimension must be positive")
        
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")
        
        logger.info("MCP Server configuration validated successfully")
    
    def to_dict(self) -> dict:
        """Convert configuration to dictionary."""
        return {
            "database": {
                "host": self.database.host,
                "port": self.database.port,
                "database": self.database.database,
                "username": self.database.username,
                # Don't include password in dict representation
            },
            "ai": {
                "embedding_model": self.ai.embedding_model,
                "llm_model": self.ai.llm_model,
                "max_tokens": self.ai.max_tokens,
                "temperature": self.ai.temperature,
            },
            "server": {
                "host": self.server.host,
                "port": self.server.port,
                "log_level": self.server.log_level,
                "debug": self.server.debug,
            },
            "vector": {
                "dimension": self.vector.dimension,
                "similarity_threshold": self.vector.similarity_threshold,
                "max_results": self.vector.max_results,
            }
        }
