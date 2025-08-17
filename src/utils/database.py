"""
Database connection and management for Idea Hub MCP Server

This module provides database connectivity and common database operations
for the MCP server to interact with the Idea Hub PostgreSQL database.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple
import asyncpg
from contextlib import asynccontextmanager

from .config import MCPConfig

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Manages database connections and operations for the MCP server."""
    
    def __init__(self, config: MCPConfig):
        self.config = config
        self.pool: Optional[asyncpg.Pool] = None
    
    async def initialize(self):
        """Initialize the database connection pool."""
        try:
            logger.info("Initializing database connection pool...")
            
            self.pool = await asyncpg.create_pool(
                host=self.config.database.host,
                port=self.config.database.port,
                user=self.config.database.username,
                password=self.config.database.password,
                database=self.config.database.database,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            
            # Test the connection
            async with self.pool.acquire() as conn:
                result = await conn.fetchval("SELECT 1")
                if result == 1:
                    logger.info("Database connection pool initialized successfully")
                else:
                    raise Exception("Database connection test failed")
                    
        except Exception as e:
            logger.error(f"Failed to initialize database connection: {e}")
            raise
    
    async def close(self):
        """Close the database connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")
    
    @asynccontextmanager
    async def get_connection(self):
        """Get a database connection from the pool."""
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
        
        async with self.pool.acquire() as connection:
            yield connection
    
    async def execute_query(self, query: str, *args) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results as list of dictionaries."""
        async with self.get_connection() as conn:
            try:
                rows = await conn.fetch(query, *args)
                return [dict(row) for row in rows]
            except Exception as e:
                logger.error(f"Query execution failed: {e}")
                logger.error(f"Query: {query}")
                logger.error(f"Args: {args}")
                raise
    
    async def execute_command(self, command: str, *args) -> str:
        """Execute an INSERT/UPDATE/DELETE command and return the result."""
        async with self.get_connection() as conn:
            try:
                result = await conn.execute(command, *args)
                return result
            except Exception as e:
                logger.error(f"Command execution failed: {e}")
                logger.error(f"Command: {command}")
                logger.error(f"Args: {args}")
                raise
    
    async def execute_fetchval(self, query: str, *args) -> Any:
        """Execute a query and return a single value."""
        async with self.get_connection() as conn:
            try:
                return await conn.fetchval(query, *args)
            except Exception as e:
                logger.error(f"Fetchval execution failed: {e}")
                logger.error(f"Query: {query}")
                logger.error(f"Args: {args}")
                raise
    
    async def execute_fetchrow(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """Execute a query and return a single row as dictionary."""
        async with self.get_connection() as conn:
            try:
                row = await conn.fetchrow(query, *args)
                return dict(row) if row else None
            except Exception as e:
                logger.error(f"Fetchrow execution failed: {e}")
                logger.error(f"Query: {query}")
                logger.error(f"Args: {args}")
                raise
    
    async def get_ideas(self, limit: int = 100, offset: int = 0, 
                       status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get ideas from the database with optional filtering."""
        query = """
            SELECT 
                id, title, description, submitter_name, submitter_email,
                department, business_value, technical_requirements,
                status, admin_notes, submission_date, last_updated,
                vector_embedding
            FROM ideas
        """
        args = []
        
        if status_filter:
            query += " WHERE status = $1"
            args.append(status_filter)
            query += " ORDER BY submission_date DESC LIMIT $2 OFFSET $3"
            args.extend([limit, offset])
        else:
            query += " ORDER BY submission_date DESC LIMIT $1 OFFSET $2"
            args.extend([limit, offset])
        
        return await self.execute_query(query, *args)
    
    async def get_idea_by_id(self, idea_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific idea by ID."""
        query = """
            SELECT 
                id, title, description, submitter_name, submitter_email,
                department, business_value, technical_requirements,
                status, admin_notes, submission_date, last_updated,
                vector_embedding
            FROM ideas
            WHERE id = $1
        """
        return await self.execute_fetchrow(query, idea_id)
    
    async def search_ideas_by_vector(self, query_vector: List[float], 
                                   threshold: float = 0.7, 
                                   limit: int = 10) -> List[Dict[str, Any]]:
        """Search for ideas using vector similarity."""
        query = """
            SELECT 
                id, title, description, submitter_name, submitter_email,
                department, business_value, technical_requirements,
                status, submission_date,
                1 - (vector_embedding <=> $1::vector) as similarity
            FROM ideas
            WHERE vector_embedding IS NOT NULL
            AND 1 - (vector_embedding <=> $1::vector) >= $2
            ORDER BY vector_embedding <=> $1::vector
            LIMIT $3
        """
        return await self.execute_query(query, query_vector, threshold, limit)
    
    async def get_contributors(self, skill_filter: Optional[List[str]] = None,
                              availability_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get contributors with optional filtering."""
        query = """
            SELECT 
                id, name, email, department, skills, experience_level,
                hours_available, preferred_project_types, bio
            FROM contributors
        """
        args = []
        conditions = []
        
        if skill_filter:
            # Search for any of the skills in the skills array
            skill_conditions = []
            for i, skill in enumerate(skill_filter):
                skill_conditions.append(f"skills ILIKE ${len(args) + 1}")
                args.append(f"%{skill}%")
            conditions.append(f"({' OR '.join(skill_conditions)})")
        
        if availability_filter:
            conditions.append(f"hours_available ILIKE ${len(args) + 1}")
            args.append(f"%{availability_filter}%")
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        return await self.execute_query(query, *args)
    
    async def update_idea_status(self, idea_id: int, status: str, 
                                admin_notes: Optional[str] = None) -> bool:
        """Update an idea's status and admin notes."""
        query = """
            UPDATE ideas 
            SET status = $2, admin_notes = $3, last_updated = CURRENT_TIMESTAMP
            WHERE id = $1
        """
        result = await self.execute_command(query, idea_id, status, admin_notes)
        return "UPDATE 1" in result
    
    async def get_idea_stats(self) -> Dict[str, Any]:
        """Get statistics about ideas in the database."""
        queries = {
            "total_ideas": "SELECT COUNT(*) FROM ideas",
            "pending_ideas": "SELECT COUNT(*) FROM ideas WHERE status = 'Under Review'",
            "approved_ideas": "SELECT COUNT(*) FROM ideas WHERE status ILIKE '%approved%'",
            "ideas_this_month": """
                SELECT COUNT(*) FROM ideas 
                WHERE submission_date >= date_trunc('month', CURRENT_DATE)
            """,
            "ideas_by_status": """
                SELECT status, COUNT(*) as count 
                FROM ideas 
                GROUP BY status 
                ORDER BY count DESC
            """,
            "ideas_by_department": """
                SELECT department, COUNT(*) as count 
                FROM ideas 
                WHERE department IS NOT NULL
                GROUP BY department 
                ORDER BY count DESC
                LIMIT 10
            """
        }
        
        stats = {}
        
        # Get single value stats
        for key in ["total_ideas", "pending_ideas", "approved_ideas", "ideas_this_month"]:
            stats[key] = await self.execute_fetchval(queries[key])
        
        # Get grouped stats
        stats["ideas_by_status"] = await self.execute_query(queries["ideas_by_status"])
        stats["ideas_by_department"] = await self.execute_query(queries["ideas_by_department"])
        
        return stats
