#!/usr/bin/env python3
"""
Database Migration Script for Idea Hub MCP Server
This script adds the missing vector_embedding column to the ideas table.
"""

import asyncio
import asyncpg
import logging
import os
import sys
from pathlib import Path

# Add the src directory to the Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir / "src"))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def run_migration():
    """Run the database migration to add vector_embedding column."""
    
    # Database connection parameters
    host = os.getenv("DATABASE_HOST", "dbproxy01.dba-001.prod.us-east-1.aws.company.com")
    port = int(os.getenv("DATABASE_PORT", "2081"))
    database = os.getenv("DATABASE_NAME", "gss_vectordb")
    username = os.getenv("DATABASE_USER", "gss_vectordb_user")
    password = os.getenv("DATABASE_PASSWORD", "Ck58ztlVcTOs4h")
    
    logger.info(f"Connecting to database: {host}:{port}/{database}")
    
    try:
        # Create connection
        conn = await asyncpg.connect(
            host=host,
            port=port,
            user=username,
            password=password,
            database=database
        )
        
        logger.info("Connected successfully!")
        
        # 1. Install pgvector extension if not exists
        logger.info("Installing pgvector extension...")
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        logger.info("✅ pgvector extension ready")
        
        # 2. Check if vector_embedding column exists
        logger.info("Checking if vector_embedding column exists...")
        column_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'ideas' 
                AND column_name = 'vector_embedding'
            )
        """)
        
        if column_exists:
            logger.info("✅ vector_embedding column already exists")
        else:
            # 3. Add the vector_embedding column
            logger.info("Adding vector_embedding column...")
            await conn.execute("""
                ALTER TABLE ideas 
                ADD COLUMN vector_embedding vector(384);
            """)
            logger.info("✅ vector_embedding column added successfully")
            
            # 4. Create index for vector operations
            logger.info("Creating vector index...")
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_ideas_vector_embedding 
                ON ideas USING ivfflat (vector_embedding vector_cosine_ops)
                WITH (lists = 100);
            """)
            logger.info("✅ Vector index created successfully")
        
        # 5. Check current state
        logger.info("Checking current ideas table state...")
        stats = await conn.fetchrow("""
            SELECT 
                COUNT(*) as total_ideas,
                COUNT(vector_embedding) as ideas_with_embeddings,
                COUNT(*) - COUNT(vector_embedding) as ideas_without_embeddings
            FROM ideas
        """)
        
        logger.info(f"📊 Database Statistics:")
        logger.info(f"   Total ideas: {stats['total_ideas']}")
        logger.info(f"   Ideas with embeddings: {stats['ideas_with_embeddings']}")
        logger.info(f"   Ideas without embeddings: {stats['ideas_without_embeddings']}")
        
        # 6. Verify table structure
        columns = await conn.fetch("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'ideas' 
            ORDER BY ordinal_position
        """)
        
        logger.info("📋 Current ideas table structure:")
        for col in columns:
            logger.info(f"   {col['column_name']}: {col['data_type']}")
        
        await conn.close()
        logger.info("🎉 Migration completed successfully!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_migration())
    sys.exit(0 if success else 1)

