#!/bin/bash

set -e

echo "🚀 Starting Idea Hub MCP Server..."

# Initialize environment variables
export HF_HOME=/opt/app-root/src/.cache/huggingface
export TRANSFORMERS_CACHE=/opt/app-root/src/.cache/huggingface
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1

# Initialize HuggingFace cache directory
if [ ! -d "$HF_HOME" ]; then
    echo "📁 Creating HuggingFace cache directory: $HF_HOME"
    mkdir -p "$HF_HOME"
fi

# Check if sentence-transformers model is cached
echo "🔍 Checking for cached embedding model..."
if [ -d "$HF_HOME/models--sentence-transformers--all-MiniLM-L6-v2" ] || [ -d "$HF_HOME/hub/models--sentence-transformers--all-MiniLM-L6-v2" ]; then
    echo "✅ all-MiniLM-L6-v2 embedding model found in cache"
    echo "🔒 Using offline mode for model loading"
else
    echo "⚠️ all-MiniLM-L6-v2 model not in cache - enabling online mode as fallback"
    export HF_HUB_OFFLINE=0
    export TRANSFORMERS_OFFLINE=0
fi

# Test MCP server import
echo "🧪 Testing MCP server import..."
/opt/app-root/src/.venv/bin/python -c "from src.main import main; print('✅ MCP server imported successfully')" || {
    echo "FastMCP dependencies not found. Please install with: pip install fastmcp"
    echo "❌ Failed to import MCP server"
    exit 1
}

echo "✅ Environment setup complete. Starting MCP server..."

# Start the MCP web server
exec /opt/app-root/src/.venv/bin/python src/web_server.py
