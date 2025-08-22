# Idea Hub MCP Server

A Model Context Protocol (MCP) server for the Idea Hub AI-powered innovation platform. This server provides tools for AI agents to interact with the idea management system, including semantic search, duplicate detection, contributor matching, and AI-powered analysis.

## Features

### Core Functionality
- **Semantic Search**: AI-powered search using vector embeddings
- **Duplicate Detection**: Identify similar ideas to prevent redundancy
- **Contributor Matching**: Match ideas with skilled contributors
- **AI Analysis**: Generate summaries, assess feasibility, and suggest improvements

### MCP Tools Available

#### Idea Management Tools
- `search_ideas` - Search for ideas using semantic, keyword, or hybrid search
- `get_idea_details` - Get detailed information about a specific idea
- `detect_duplicates` - Detect duplicate or similar ideas
- `analyze_idea_trends` - Analyze trends in submitted ideas

#### Contributor Tools
- `search_contributors` - Search for contributors by skills or availability
- `match_contributors_to_idea` - Find contributors that match an idea's requirements

#### AI Analysis Tools
- `generate_idea_summary` - Generate AI summary of an idea
- `assess_idea_feasibility` - Assess technical and business feasibility
- `suggest_improvements` - Suggest improvements for an idea

## Architecture

### Technology Stack
- **MCP Protocol**: Model Context Protocol for AI agent interactions
- **Database**: PostgreSQL with pgvector extension for vector operations
- **AI Models**: 
  - Google Gemini for reasoning and text generation
  - HuggingFace Sentence Transformers for embeddings
- **Vector Operations**: Sentence Transformers with PostgreSQL pgvector
- **Language**: Python 3.12+ with async/await support

### Key Components
- **Server Core**: Main MCP server implementation (`src/server.py`)
- **Tool Modules**: Specialized tools for different domains (`src/tools/`)
- **Database Layer**: Async PostgreSQL operations (`src/utils/database.py`)
- **Configuration**: Environment-based configuration (`src/utils/config.py`)

## Installation

### Prerequisites
- Python 3.12+
- PostgreSQL with pgvector extension
- Google API key for Gemini AI
- HuggingFace account (optional, for some models)

### Setup
1. Clone the repository:
   ```bash
   git clone git@gitlab.cee.company.com:nitsingh/idea_hub_mcp_server.git
   cd idea-hub-mcp-server
   ```

2. Install dependencies:
   ```bash
   pip install -e .
   ```

3. Set up environment variables:
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

4. Set up the database:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

## Configuration

### Environment Variables
Create a `.env` file with the following variables:

```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=idea_hub
DB_USER=postgres
DB_PASSWORD=your_password

# AI Configuration
GOOGLE_API_KEY=your_google_api_key
HUGGINGFACE_TOKEN=your_hf_token  # Optional
EMBEDDING_MODEL=all-MiniLM-L6-v2
LLM_MODEL=gemini-pro

# Server Configuration
SERVER_HOST=localhost
SERVER_PORT=8000
LOG_LEVEL=INFO
DEBUG=false

# Vector Configuration
VECTOR_DIMENSION=384
SIMILARITY_THRESHOLD=0.7
MAX_VECTOR_RESULTS=10
```

## Usage

### Running the Server
```bash
# Run directly
python -m src.main

# Or using the installed script
idea-hub-mcp-server
```

### Connecting to the Server
The server implements the MCP protocol and can be used by any MCP-compatible AI agent or client.

Example MCP client connection:
```json
{
  "method": "tools/list",
  "params": {}
}
```

### Tool Usage Examples

#### Search Ideas
```json
{
  "method": "tools/call",
  "params": {
    "name": "search_ideas",
    "arguments": {
      "query": "machine learning automation",
      "search_type": "semantic",
      "limit": 5
    }
  }
}
```

#### Detect Duplicates
```json
{
  "method": "tools/call",
  "params": {
    "name": "detect_duplicates",
    "arguments": {
      "title": "AI-powered chatbot for customer service",
      "description": "Implement an intelligent chatbot using natural language processing...",
      "threshold": 0.8
    }
  }
}
```

#### Match Contributors
```json
{
  "method": "tools/call",
  "params": {
    "name": "match_contributors_to_idea",
    "arguments": {
      "idea_id": 123,
      "required_skills": ["Python", "Machine Learning", "API Development"],
      "max_contributors": 3
    }
  }
}
```

## Development

### Project Structure
```
idea-hub-mcp-server/
├── src/
│   ├── main.py              # Entry point
│   ├── server.py            # Main MCP server
│   ├── tools/               # Tool implementations
│   │   ├── idea_tools.py    # Idea management
│   │   ├── vector_tools.py  # Vector operations
│   │   ├── contributor_tools.py  # Contributor matching
│   │   └── ai_tools.py      # AI analysis
│   └── utils/               # Utilities
│       ├── config.py        # Configuration
│       └── database.py      # Database operations
├── tests/                   # Test suite
├── pyproject.toml          # Project configuration
├── env.example             # Environment template
└── README.md               # This file
```

### Running Tests
```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=src
```

### Code Quality
```bash
# Format code
ruff format

# Lint code
ruff check

# Type checking
mypy src
```

## Integration with Idea Hub

This MCP server is designed to work alongside the main Idea Hub application, providing AI agent capabilities to:

1. **Enhance Idea Submission**: Detect duplicates and suggest improvements during submission
2. **Smart Search**: Enable semantic search across all ideas
3. **Contributor Matching**: Automatically suggest contributors for new ideas
4. **AI Analysis**: Provide automated feasibility assessments and summaries

## Team

- **Designed By**: Nitish Singh ([Company Rover Profile](https://rover.company.com/people/profile/nitsingh))
- **Key Contributors**: 
  - Rishika Kumar ([Company Rover Profile](https://rover.company.com/people/profile/rishika))
  - Shubham Chilhate ([Company Rover Profile](https://rover.company.com/people/profile/shubham))

## License

This project is part of Company's innovation initiatives and follows internal licensing guidelines.

## Support

For questions or issues, please contact the development team or create an issue in the project repository.