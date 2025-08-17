#!/bin/bash

set -e

echo "🏗️  Building Idea Hub MCP Server container image..."

# Build with AMD64 architecture for OpenShift compatibility
podman build --arch amd64 -t idea-hub-mcp-server:latest -f Containerfile .

echo "🏷️  Tagging image for Quay..."
podman tag idea-hub-mcp-server:latest quay.io/rhn-support-nitsingh/idea-hub-mcp-server:latest

echo "📤 Pushing image to Quay..."
podman push quay.io/rhn-support-nitsingh/idea-hub-mcp-server:latest

echo "✅ Image pushed successfully!"
echo "📍 Available at: quay.io/rhn-support-nitsingh/idea-hub-mcp-server:latest"
