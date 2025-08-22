-- Fix Database Schema for Idea Hub MCP Server
-- This script adds the missing vector_embedding column to the ideas table

-- 1. Ensure pgvector extension is installed
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Add the vector_embedding column to the ideas table
-- The column will store 384-dimensional vectors (for all-MiniLM-L6-v2 model)
ALTER TABLE ideas 
ADD COLUMN IF NOT EXISTS vector_embedding vector(384);

-- 3. Create an index for faster vector similarity searches
CREATE INDEX IF NOT EXISTS idx_ideas_vector_embedding 
ON ideas USING ivfflat (vector_embedding vector_cosine_ops)
WITH (lists = 100);

-- 4. Verify the column was added successfully
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'ideas' 
AND column_name = 'vector_embedding';

-- 5. Check if there are any existing ideas that need embeddings generated
SELECT 
    COUNT(*) as total_ideas,
    COUNT(vector_embedding) as ideas_with_embeddings,
    COUNT(*) - COUNT(vector_embedding) as ideas_without_embeddings
FROM ideas;

