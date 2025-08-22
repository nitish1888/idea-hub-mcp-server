#!/usr/bin/env python3
"""
Simple MCP Client Test Script

This script demonstrates how to interact with the Idea Hub MCP server
and test its tools.
"""

import asyncio
import json
import subprocess
import sys
from typing import Dict, Any

class SimpleMCPClient:
    """Simple MCP client for testing the Idea Hub MCP server."""
    
    def __init__(self):
        self.process = None
    
    async def connect(self):
        """Connect to the MCP server."""
        print("🔌 Connecting to Idea Hub MCP Server...")
        
        # Start the MCP server process
        self.process = await asyncio.create_subprocess_exec(
            sys.executable, "-m", "src.main",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd="/Users/nitsingh/idea_hub_updated/idea-hub-mcp-server"
        )
        
        print("✅ Connected to MCP server!")
    
    async def send_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send a request to the MCP server."""
        if not self.process:
            raise RuntimeError("Not connected to MCP server")
        
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or {}
        }
        
        # Send request
        request_json = json.dumps(request) + "\n"
        self.process.stdin.write(request_json.encode())
        await self.process.stdin.drain()
        
        # Read response
        response_line = await self.process.stdout.readline()
        response = json.loads(response_line.decode())
        
        return response
    
    async def list_tools(self):
        """List all available MCP tools."""
        print("\n📋 Listing available MCP tools...")
        try:
            response = await self.send_request("tools/list")
            
            if "result" in response:
                tools = response["result"]["tools"]
                print(f"✅ Found {len(tools)} tools:")
                
                for tool in tools:
                    print(f"  🔧 {tool['name']}: {tool['description']}")
                    
                return tools
            else:
                print(f"❌ Error: {response.get('error', 'Unknown error')}")
                return []
        except Exception as e:
            print(f"❌ Failed to list tools: {e}")
            return []
    
    async def test_search_ideas(self, query: str = "AI automation"):
        """Test the search_ideas tool."""
        print(f"\n🔍 Testing search_ideas with query: '{query}'...")
        try:
            response = await self.send_request("tools/call", {
                "name": "search_ideas",
                "arguments": {
                    "query": query,
                    "search_type": "semantic",
                    "limit": 3
                }
            })
            
            if "result" in response:
                print("✅ Search results:")
                result = json.loads(response["result"][0]["text"])
                
                if "results" in result:
                    for idea in result["results"]:
                        print(f"  💡 {idea['title']} (ID: {idea['id']})")
                        print(f"     📝 {idea['description'][:100]}...")
                        if 'similarity_score' in idea:
                            print(f"     📊 Similarity: {idea['similarity_score']}")
                        print()
                else:
                    print(f"  📄 Result: {result}")
            else:
                print(f"❌ Error: {response.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"❌ Failed to search ideas: {e}")
    
    async def test_database_connection(self):
        """Test database connectivity through embedding stats."""
        print("\n🗄️  Testing database connection...")
        try:
            response = await self.send_request("tools/call", {
                "name": "get_embedding_stats",
                "arguments": {}
            })
            
            if "result" in response:
                print("✅ Database connection successful!")
                result = json.loads(response["result"][0]["text"])
                
                if "total_ideas" in result:
                    print(f"  📊 Total ideas in database: {result['total_ideas']}")
                    print(f"  🎯 Ideas with embeddings: {result['ideas_with_embeddings']}")
                    print(f"  📈 Coverage: {result['coverage_percentage']}%")
                else:
                    print(f"  📄 Stats: {result}")
            else:
                print(f"❌ Database error: {response.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"❌ Failed to test database: {e}")
    
    async def close(self):
        """Close the connection to the MCP server."""
        if self.process:
            self.process.terminate()
            await self.process.wait()
            print("🔌 Disconnected from MCP server")

async def main():
    """Main test function."""
    print("🚀 Idea Hub MCP Server Test Client")
    print("=" * 50)
    
    client = SimpleMCPClient()
    
    try:
        # Connect to server
        await client.connect()
        
        # Test basic functionality
        await client.list_tools()
        await client.test_database_connection()
        await client.test_search_ideas()
        
        print("\n✅ All tests completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())


