"""
Idea Hub MCP Server Implementation

This module implements the core MCP server for the Idea Hub platform using FastMCP.
It provides tools for AI agents to interact with the idea management system,
including semantic search, duplicate detection, contributor matching, and more.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import os
import sys
from pathlib import Path

# Import MCP components
try:
    from fastmcp import FastMCP
    from typing_extensions import Annotated
except ImportError:
    print("FastMCP dependencies not found. Please install with: pip install fastmcp")
    sys.exit(1)

# Import our custom tools and utilities
from tools.idea_tools import IdeaTools
from tools.vector_tools import VectorTools
from tools.contributor_tools import ContributorTools
from tools.ai_tools import AITools
from utils.database import DatabaseConnection
from utils.config import MCPConfig

logger = logging.getLogger(__name__)


@dataclass
class ServerContext:
    """Context object to share resources between tools."""
    db_connection: DatabaseConnection
    config: MCPConfig
    idea_tools: IdeaTools
    vector_tools: VectorTools
    contributor_tools: ContributorTools
    ai_tools: AITools


class IdeaHubMCPServer:
    """Main MCP server class for Idea Hub using FastMCP."""
    
    def __init__(self):
        self.app = FastMCP("Idea Hub MCP Server")
        self.context: Optional[ServerContext] = None
        self._setup_tools()
    
    def _setup_tools(self):
        """Set up MCP tools using FastMCP decorators."""
        
        @self.app.tool()
        async def search_ideas(
            query: Annotated[str, "Search query for ideas"],
            search_type: Annotated[str, "Type of search (semantic, keyword, hybrid)"] = "hybrid",
            limit: Annotated[int, "Maximum number of results"] = 10,
            status_filter: Annotated[Optional[str], "Optional status filter"] = None
        ) -> Dict[str, Any]:
            """Search for ideas using semantic search or keywords."""
            if not self.context:
                await self._initialize_context()
            
            return await self.context.idea_tools.search_ideas(
                query=query,
                search_type=search_type,
                limit=limit,
                status_filter=status_filter
            )
        
        @self.app.tool()
        async def get_idea_details(
            idea_id: Annotated[int, "ID of the idea to get details for"]
        ) -> Dict[str, Any]:
            """Get detailed information about a specific idea."""
            if not self.context:
                await self._initialize_context()
            
            return await self.context.idea_tools.get_idea_details(idea_id)
        
        @self.app.tool()
        async def detect_duplicates(
            title: Annotated[str, "Title of the idea to check for duplicates"],
            description: Annotated[str, "Description of the idea to check"],
            threshold: Annotated[float, "Similarity threshold (0.0-1.0)"] = 0.8
        ) -> Dict[str, Any]:
            """Detect duplicate or similar ideas."""
            if not self.context:
                await self._initialize_context()
            
            return await self.context.idea_tools.detect_duplicates(
                title=title,
                description=description,
                threshold=threshold
            )
        
        @self.app.tool()
        async def analyze_idea_trends(
            time_period: Annotated[str, "Time period for analysis (7days, 30days, 90days, 1year)"] = "30days",
            category: Annotated[Optional[str], "Optional category filter"] = None
        ) -> Dict[str, Any]:
            """Analyze trends in submitted ideas."""
            if not self.context:
                await self._initialize_context()
            
            return await self.context.idea_tools.analyze_trends(
                time_period=time_period,
                category=category
            )
        
        @self.app.tool()
        async def search_contributors(
            skills: Annotated[Optional[List[str]], "List of required skills"] = None,
            availability: Annotated[Optional[str], "Required availability"] = None,
            experience_level: Annotated[Optional[str], "Required experience level"] = None,
            department: Annotated[Optional[str], "Department filter"] = None,
            limit: Annotated[int, "Maximum number of results"] = 20
        ) -> Dict[str, Any]:
            """Search for contributors by skills or availability."""
            if not self.context:
                await self._initialize_context()
            
            return await self.context.contributor_tools.search_contributors(
                skills=skills,
                availability=availability,
                experience_level=experience_level,
                department=department,
                limit=limit
            )
        
        @self.app.tool()
        async def match_contributors_to_idea(
            idea_id: Annotated[int, "ID of the idea to match contributors to"],
            required_skills: Annotated[Optional[List[str]], "List of required skills"] = None,
            max_contributors: Annotated[int, "Maximum number of contributors"] = 5
        ) -> Dict[str, Any]:
            """Find contributors that match an idea's requirements."""
            if not self.context:
                await self._initialize_context()
            
            return await self.context.contributor_tools.match_to_idea(
                idea_id=idea_id,
                required_skills=required_skills,
                max_contributors=max_contributors
            )
        
        @self.app.tool()
        async def generate_idea_summary(
            idea_id: Annotated[int, "ID of the idea to summarize"],
            summary_type: Annotated[str, "Type of summary (brief, detailed, technical, business)"] = "brief"
        ) -> Dict[str, Any]:
            """Generate AI summary of an idea."""
            if not self.context:
                await self._initialize_context()
            
            return await self.context.ai_tools.generate_summary(
                idea_id=idea_id,
                summary_type=summary_type
            )
        
        @self.app.tool()
        async def assess_idea_feasibility(
            idea_id: Annotated[int, "ID of the idea to assess"]
        ) -> Dict[str, Any]:
            """Assess the technical and business feasibility of an idea."""
            if not self.context:
                await self._initialize_context()
            
            return await self.context.ai_tools.assess_feasibility(idea_id)
        
        @self.app.tool()
        async def suggest_improvements(
            idea_id: Annotated[int, "ID of the idea to improve"],
            focus_area: Annotated[str, "Focus area (technical, business, user_experience, scalability)"] = "technical"
        ) -> Dict[str, Any]:
            """Suggest improvements for an idea."""
            if not self.context:
                await self._initialize_context()
            
            return await self.context.ai_tools.suggest_improvements(
                idea_id=idea_id,
                focus_area=focus_area
            )
        
        @self.app.tool()
        async def get_embedding_stats() -> Dict[str, Any]:
            """Get statistics about vector embeddings in the database."""
            if not self.context:
                await self._initialize_context()
            
            return await self.context.vector_tools.get_embedding_stats()
        
        @self.app.tool()
        async def rebuild_embeddings(
            batch_size: Annotated[int, "Number of ideas to process in each batch"] = 10
        ) -> Dict[str, Any]:
            """Rebuild embeddings for all ideas in the database."""
            if not self.context:
                await self._initialize_context()
            
            return await self.context.vector_tools.rebuild_all_embeddings(batch_size)
    
    async def _initialize_context(self):
        """Initialize the server context with all required components."""
        if self.context:
            return  # Already initialized
            
        logger.info("Initializing MCP server context...")
        
        try:
            # Load configuration
            config = MCPConfig()
            
            # Initialize database connection
            db_connection = DatabaseConnection(config)
            await db_connection.initialize()
            
            # Initialize tool classes
            idea_tools = IdeaTools(db_connection, config)
            vector_tools = VectorTools(db_connection, config)
            contributor_tools = ContributorTools(db_connection, config)
            ai_tools = AITools(db_connection, config)
            
            # Create context
            self.context = ServerContext(
                db_connection=db_connection,
                config=config,
                idea_tools=idea_tools,
                vector_tools=vector_tools,
                contributor_tools=contributor_tools,
                ai_tools=ai_tools
            )
            
            logger.info("MCP server context initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize server context: {e}")
            raise
    
    async def run(self):
        """Run the MCP server."""
        logger.info("Starting Idea Hub MCP Server...")
        
        try:
            # Initialize context
            await self._initialize_context()
            
            # Run the FastMCP server
            await self.app.run()
            
        except Exception as e:
            logger.error(f"Server error: {e}")
            raise
        finally:
            # Cleanup
            if self.context and self.context.db_connection:
                await self.context.db_connection.close()
    
    def get_app(self):
        """Get the FastMCP app instance."""
        return self.app