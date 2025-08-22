#!/usr/bin/env python3
"""
Idea Hub MCP Server - Main Entry Point

This is the main entry point for the Idea Hub MCP (Model Context Protocol) server.
It initializes and runs the MCP server with all the tools and capabilities needed
for the AI-powered innovation platform.

Based on Company's dataverse-mcp-server architecture but customized for Idea Hub.
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add the src directory to the Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from server import IdeaHubMCPServer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for the Idea Hub MCP server."""
    try:
        logger.info("Starting Idea Hub MCP Server...")
        
        # Initialize the MCP server
        server = IdeaHubMCPServer()
        
        # Get the FastMCP app and run it
        app = server.get_app()
        
        # Run the server using FastMCP's built-in runner
        app.run()
        
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise


if __name__ == "__main__":
    main()
