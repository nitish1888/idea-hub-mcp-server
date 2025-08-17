"""
Vector Operations Tools for MCP Server

This module provides tools for vector embedding generation and similarity operations
using HuggingFace models and PostgreSQL pgvector extension.
"""

import logging
from typing import List, Optional, Dict, Any
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None
    logging.warning("sentence-transformers not installed. Vector operations will be limited.")

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import DatabaseConnection
from utils.config import MCPConfig

logger = logging.getLogger(__name__)


class VectorTools:
    """Tools for vector embedding and similarity operations."""
    
    def __init__(self, db: DatabaseConnection, config: MCPConfig):
        self.db = db
        self.config = config
        self.embedding_model: Optional[SentenceTransformer] = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the embedding model."""
        try:
            if SentenceTransformer is None:
                logger.warning("SentenceTransformer not available. Vector operations disabled.")
                return
            
            logger.info(f"Loading embedding model: {self.config.ai.embedding_model}")
            self.embedding_model = SentenceTransformer(self.config.ai.embedding_model)
            logger.info("Embedding model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            self.embedding_model = None
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate vector embedding for the given text.
        
        Args:
            text: Input text to generate embedding for
            
        Returns:
            List of float values representing the embedding vector
        """
        try:
            if not self.embedding_model:
                raise RuntimeError("Embedding model not available")
            
            # Clean and prepare text
            cleaned_text = text.strip()
            if not cleaned_text:
                raise ValueError("Empty text provided")
            
            # Generate embedding
            embedding = self.embedding_model.encode(cleaned_text)
            
            # Convert to list of floats
            embedding_list = embedding.tolist()
            
            logger.debug(f"Generated embedding with dimension: {len(embedding_list)}")
            
            return embedding_list
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    async def generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch.
        
        Args:
            texts: List of input texts
            
        Returns:
            List of embedding vectors
        """
        try:
            if not self.embedding_model:
                raise RuntimeError("Embedding model not available")
            
            if not texts:
                return []
            
            # Clean texts
            cleaned_texts = [text.strip() for text in texts if text.strip()]
            
            if not cleaned_texts:
                raise ValueError("No valid texts provided")
            
            # Generate embeddings in batch
            embeddings = self.embedding_model.encode(cleaned_texts)
            
            # Convert to list of lists
            embeddings_list = [embedding.tolist() for embedding in embeddings]
            
            logger.info(f"Generated {len(embeddings_list)} embeddings in batch")
            
            return embeddings_list
            
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            raise
    
    async def calculate_similarity(self, embedding1: List[float], 
                                 embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        try:
            # Convert to numpy arrays
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            
            # Ensure similarity is between 0 and 1
            similarity = max(0.0, min(1.0, similarity))
            
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0
    
    async def find_similar_vectors(self, query_embedding: List[float],
                                 table_name: str = "ideas",
                                 vector_column: str = "vector_embedding",
                                 threshold: float = 0.7,
                                 limit: int = 10) -> List[Dict[str, Any]]:
        """
        Find similar vectors in the database using pgvector.
        
        Args:
            query_embedding: Query vector to search for
            table_name: Name of the table to search in
            vector_column: Name of the vector column
            threshold: Minimum similarity threshold
            limit: Maximum number of results
            
        Returns:
            List of similar records with similarity scores
        """
        try:
            query = f"""
                SELECT 
                    *,
                    1 - ({vector_column} <=> $1::vector) as similarity
                FROM {table_name}
                WHERE {vector_column} IS NOT NULL
                AND 1 - ({vector_column} <=> $1::vector) >= $2
                ORDER BY {vector_column} <=> $1::vector
                LIMIT $3
            """
            
            results = await self.db.execute_query(query, query_embedding, threshold, limit)
            
            return results
            
        except Exception as e:
            logger.error(f"Error finding similar vectors: {e}")
            return []
    
    async def update_idea_embedding(self, idea_id: int, title: str, description: str) -> bool:
        """
        Update the vector embedding for a specific idea.
        
        Args:
            idea_id: ID of the idea to update
            title: Title of the idea
            description: Description of the idea
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Combine title and description
            content = f"{title} {description}"
            
            # Generate embedding
            embedding = await self.generate_embedding(content)
            
            # Update the database
            query = """
                UPDATE ideas 
                SET vector_embedding = $2::vector,
                    last_updated = CURRENT_TIMESTAMP
                WHERE id = $1
            """
            
            result = await self.db.execute_command(query, idea_id, embedding)
            
            success = "UPDATE 1" in result
            
            if success:
                logger.info(f"Updated embedding for idea {idea_id}")
            else:
                logger.warning(f"No idea found with ID {idea_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error updating idea embedding: {e}")
            return False
    
    async def rebuild_all_embeddings(self, batch_size: int = 10) -> Dict[str, Any]:
        """
        Rebuild embeddings for all ideas in the database.
        
        Args:
            batch_size: Number of ideas to process in each batch
            
        Returns:
            Dictionary with rebuild statistics
        """
        try:
            logger.info("Starting embedding rebuild for all ideas")
            
            # Get all ideas without embeddings or with old embeddings
            query = """
                SELECT id, title, description
                FROM ideas
                ORDER BY id
            """
            
            ideas = await self.db.execute_query(query)
            total_ideas = len(ideas)
            
            if total_ideas == 0:
                return {
                    "total_ideas": 0,
                    "processed": 0,
                    "successful": 0,
                    "failed": 0,
                    "message": "No ideas found in database"
                }
            
            processed = 0
            successful = 0
            failed = 0
            
            # Process in batches
            for i in range(0, total_ideas, batch_size):
                batch = ideas[i:i + batch_size]
                
                try:
                    # Prepare texts for batch embedding
                    texts = [f"{idea['title']} {idea['description']}" for idea in batch]
                    
                    # Generate embeddings in batch
                    embeddings = await self.generate_batch_embeddings(texts)
                    
                    # Update database
                    for j, (idea, embedding) in enumerate(zip(batch, embeddings)):
                        try:
                            update_query = """
                                UPDATE ideas 
                                SET vector_embedding = $2::vector,
                                    last_updated = CURRENT_TIMESTAMP
                                WHERE id = $1
                            """
                            
                            result = await self.db.execute_command(update_query, idea['id'], embedding)
                            
                            if "UPDATE 1" in result:
                                successful += 1
                            else:
                                failed += 1
                            
                            processed += 1
                            
                        except Exception as e:
                            logger.error(f"Failed to update embedding for idea {idea['id']}: {e}")
                            failed += 1
                            processed += 1
                    
                    logger.info(f"Processed batch {i // batch_size + 1}/{(total_ideas + batch_size - 1) // batch_size}")
                    
                except Exception as e:
                    logger.error(f"Failed to process batch starting at index {i}: {e}")
                    failed += len(batch)
                    processed += len(batch)
            
            result = {
                "total_ideas": total_ideas,
                "processed": processed,
                "successful": successful,
                "failed": failed,
                "success_rate": round((successful / processed) * 100, 2) if processed > 0 else 0,
                "message": f"Embedding rebuild completed. {successful}/{processed} ideas updated successfully."
            }
            
            logger.info(f"Embedding rebuild completed: {result}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error rebuilding embeddings: {e}")
            return {
                "error": str(e),
                "total_ideas": 0,
                "processed": 0,
                "successful": 0,
                "failed": 0
            }
    
    async def get_embedding_stats(self) -> Dict[str, Any]:
        """
        Get statistics about vector embeddings in the database.
        
        Returns:
            Dictionary with embedding statistics
        """
        try:
            # Get embedding statistics
            stats_query = """
                SELECT 
                    COUNT(*) as total_ideas,
                    COUNT(vector_embedding) as ideas_with_embeddings,
                    COUNT(*) - COUNT(vector_embedding) as ideas_without_embeddings
                FROM ideas
            """
            
            stats = await self.db.execute_fetchrow(stats_query)
            
            # Calculate percentage
            total = stats["total_ideas"]
            with_embeddings = stats["ideas_with_embeddings"]
            
            coverage_percentage = round((with_embeddings / total) * 100, 2) if total > 0 else 0
            
            result = {
                "total_ideas": total,
                "ideas_with_embeddings": with_embeddings,
                "ideas_without_embeddings": stats["ideas_without_embeddings"],
                "coverage_percentage": coverage_percentage,
                "embedding_model": self.config.ai.embedding_model,
                "vector_dimension": self.config.vector.dimension,
                "model_available": self.embedding_model is not None
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting embedding stats: {e}")
            return {
                "error": str(e),
                "total_ideas": 0,
                "ideas_with_embeddings": 0,
                "ideas_without_embeddings": 0,
                "coverage_percentage": 0
            }
