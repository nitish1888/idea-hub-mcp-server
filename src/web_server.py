"""
Web Interface for Idea Hub MCP Server

This provides a simple web interface to interact with the MCP server tools
for testing and demonstration purposes.
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import asyncio
import logging

from server import IdeaHubMCPServer

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Idea Hub MCP Server API",
    description="Web interface for the Idea Hub MCP Server",
    version="1.0.0"
)

# Global MCP server instance
mcp_server: Optional[IdeaHubMCPServer] = None

@app.on_event("startup")
async def startup_event():
    """Initialize the MCP server on startup."""
    global mcp_server
    try:
        logger.info("Initializing MCP server...")
        mcp_server = IdeaHubMCPServer()
        await mcp_server._initialize_context()
        logger.info("MCP server initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize MCP server: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    global mcp_server
    if mcp_server and mcp_server.context and mcp_server.context.db_connection:
        await mcp_server.context.db_connection.close()
        logger.info("MCP server closed")

# Request/Response models
class SearchRequest(BaseModel):
    query: str
    search_type: str = "hybrid"
    limit: int = 10
    status_filter: Optional[str] = None

class DuplicateCheckRequest(BaseModel):
    title: str
    description: str
    threshold: float = 0.8

class ContributorSearchRequest(BaseModel):
    skills: Optional[List[str]] = None
    availability: Optional[str] = None
    experience_level: Optional[str] = None
    limit: int = 20

class SummaryRequest(BaseModel):
    idea_id: int
    summary_type: str = "brief"

@app.get("/", response_class=HTMLResponse)
async def get_web_interface():
    """Serve a simple web interface."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Idea Hub MCP Server</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #ee0000; text-align: center; margin-bottom: 30px; }
            .section { margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 5px; background-color: #fafafa; }
            .section h3 { color: #333; margin-top: 0; }
            .endpoint { margin: 10px 0; padding: 10px; background-color: white; border-left: 4px solid #ee0000; }
            .method { font-weight: bold; color: #ee0000; }
            .path { font-family: monospace; background-color: #f0f0f0; padding: 2px 5px; border-radius: 3px; }
            .description { margin-top: 5px; color: #666; }
            code { background-color: #f0f0f0; padding: 2px 5px; border-radius: 3px; font-family: monospace; }
            .status { padding: 10px; background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 5px; color: #155724; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Idea Hub MCP Server</h1>
            
            <div class="status">
                ✅ <strong>Server Status:</strong> Running and connected to database
            </div>
            
            <div class="section">
                <h3>🔧 Available MCP Tools</h3>
                <p>The following tools are available through the MCP protocol:</p>
                
                <div class="endpoint">
                    <span class="method">POST</span> <span class="path">/api/search-ideas</span>
                    <div class="description">Search for ideas using semantic, keyword, or hybrid search</div>
                </div>
                
                <div class="endpoint">
                    <span class="method">GET</span> <span class="path">/api/idea/{idea_id}</span>
                    <div class="description">Get detailed information about a specific idea</div>
                </div>
                
                <div class="endpoint">
                    <span class="method">POST</span> <span class="path">/api/detect-duplicates</span>
                    <div class="description">Detect duplicate or similar ideas</div>
                </div>
                
                <div class="endpoint">
                    <span class="method">POST</span> <span class="path">/api/search-contributors</span>
                    <div class="description">Search for contributors by skills or availability</div>
                </div>
                
                <div class="endpoint">
                    <span class="method">POST</span> <span class="path">/api/generate-summary</span>
                    <div class="description">Generate AI summary of an idea</div>
                </div>
                
                <div class="endpoint">
                    <span class="method">GET</span> <span class="path">/api/embedding-stats</span>
                    <div class="description">Get statistics about vector embeddings</div>
                </div>
            </div>
            
            <div class="section">
                <h3>📚 API Documentation</h3>
                <p>Interactive API documentation is available at:</p>
                <ul>
                    <li><a href="/docs" target="_blank">Swagger UI Documentation</a></li>
                    <li><a href="/redoc" target="_blank">ReDoc Documentation</a></li>
                </ul>
            </div>
            
            <div class="section">
                <h3>🔌 MCP Client Access</h3>
                <p>To connect an MCP client:</p>
                <code>python -m src.main</code>
                <p>The server uses STDIO transport for MCP protocol communication.</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html_content

@app.post("/api/search-ideas")
async def search_ideas(request: SearchRequest):
    """Search for ideas using the MCP server."""
    if not mcp_server or not mcp_server.context:
        raise HTTPException(status_code=500, detail="MCP server not initialized")
    
    try:
        result = await mcp_server.context.idea_tools.search_ideas(
            query=request.query,
            search_type=request.search_type,
            limit=request.limit,
            status_filter=request.status_filter
        )
        return result
    except Exception as e:
        logger.error(f"Error searching ideas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/idea/{idea_id}")
async def get_idea_details(idea_id: int):
    """Get detailed information about a specific idea."""
    if not mcp_server or not mcp_server.context:
        raise HTTPException(status_code=500, detail="MCP server not initialized")
    
    try:
        result = await mcp_server.context.idea_tools.get_idea_details(idea_id)
        return result
    except Exception as e:
        logger.error(f"Error getting idea details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/detect-duplicates")
async def detect_duplicates(request: DuplicateCheckRequest):
    """Detect duplicate or similar ideas."""
    if not mcp_server or not mcp_server.context:
        raise HTTPException(status_code=500, detail="MCP server not initialized")
    
    try:
        result = await mcp_server.context.idea_tools.detect_duplicates(
            title=request.title,
            description=request.description,
            threshold=request.threshold
        )
        return result
    except Exception as e:
        logger.error(f"Error detecting duplicates: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/search-contributors")
async def search_contributors(request: ContributorSearchRequest):
    """Search for contributors by skills or availability."""
    if not mcp_server or not mcp_server.context:
        raise HTTPException(status_code=500, detail="MCP server not initialized")
    
    try:
        result = await mcp_server.context.contributor_tools.search_contributors(
            skills=request.skills,
            availability=request.availability,
            experience_level=request.experience_level,
            limit=request.limit
        )
        return result
    except Exception as e:
        logger.error(f"Error searching contributors: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-summary")
async def generate_summary(request: SummaryRequest):
    """Generate AI summary of an idea."""
    if not mcp_server or not mcp_server.context:
        raise HTTPException(status_code=500, detail="MCP server not initialized")
    
    try:
        result = await mcp_server.context.ai_tools.generate_summary(
            idea_id=request.idea_id,
            summary_type=request.summary_type
        )
        return result
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/embedding-stats")
async def get_embedding_stats():
    """Get statistics about vector embeddings in the database."""
    if not mcp_server or not mcp_server.context:
        raise HTTPException(status_code=500, detail="MCP server not initialized")
    
    try:
        result = await mcp_server.context.vector_tools.get_embedding_stats()
        return result
    except Exception as e:
        logger.error(f"Error getting embedding stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Request model for rebuild
class RebuildRequest(BaseModel):
    batch_size: int = 10

@app.post("/api/rebuild-embeddings")
async def rebuild_embeddings(request: RebuildRequest):
    """Rebuild embeddings for all ideas in the database."""
    if not mcp_server or not mcp_server.context:
        raise HTTPException(status_code=500, detail="MCP server not initialized")
    
    try:
        result = await mcp_server.context.vector_tools.rebuild_all_embeddings(request.batch_size)
        return result
    except Exception as e:
        logger.error(f"Error rebuilding embeddings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    if not mcp_server or not mcp_server.context:
        return {"status": "error", "message": "MCP server not initialized"}
    
    try:
        # Test database connection
        stats = await mcp_server.context.vector_tools.get_embedding_stats()
        return {
            "status": "healthy",
            "mcp_server": "running",
            "database": "connected",
            "total_ideas": stats.get("total_ideas", 0)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    print("🌐 Starting Idea Hub MCP Server Web Interface...")
    print("📍 Access at: http://localhost:8000")
    print("📚 API Docs at: http://localhost:8000/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)


