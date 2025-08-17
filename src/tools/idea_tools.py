"""
Idea Management Tools for MCP Server

This module provides tools for managing ideas in the Idea Hub platform,
including searching, duplicate detection, trend analysis, and more.
"""

import logging
from typing import Any, Dict, List, Optional
import json
from datetime import datetime, timedelta

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import DatabaseConnection
from utils.config import MCPConfig

logger = logging.getLogger(__name__)


class IdeaTools:
    """Tools for idea management operations."""
    
    def __init__(self, db: DatabaseConnection, config: MCPConfig):
        self.db = db
        self.config = config
        # Import VectorTools here to avoid circular imports
        from .vector_tools import VectorTools
        self.vector_tools = VectorTools(db, config)
    
    async def search_ideas(self, query: str, search_type: str = "hybrid", 
                          limit: int = 10, status_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        Search for ideas using different search strategies.
        
        Args:
            query: Search query string
            search_type: Type of search ("semantic", "keyword", "hybrid")
            limit: Maximum number of results to return
            status_filter: Optional status filter
            
        Returns:
            Dictionary containing search results and metadata
        """
        try:
            logger.info(f"Searching ideas: query='{query}', type={search_type}, limit={limit}")
            
            results = []
            
            if search_type == "semantic":
                results = await self._semantic_search(query, limit, status_filter)
            elif search_type == "keyword":
                results = await self._keyword_search(query, limit, status_filter)
            elif search_type == "hybrid":
                # Combine semantic and keyword search results
                semantic_results = await self._semantic_search(query, limit // 2, status_filter)
                keyword_results = await self._keyword_search(query, limit // 2, status_filter)
                
                # Merge and deduplicate results
                seen_ids = set()
                for result in semantic_results + keyword_results:
                    if result["id"] not in seen_ids:
                        results.append(result)
                        seen_ids.add(result["id"])
                        if len(results) >= limit:
                            break
            else:
                raise ValueError(f"Unknown search type: {search_type}")
            
            return {
                "query": query,
                "search_type": search_type,
                "total_results": len(results),
                "results": results,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error searching ideas: {e}")
            return {
                "error": str(e),
                "query": query,
                "search_type": search_type,
                "results": []
            }
    
    async def _semantic_search(self, query: str, limit: int, 
                              status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Perform semantic search using vector embeddings."""
        try:
            # Generate embedding for the query
            query_embedding = await self.vector_tools.generate_embedding(query)
            
            # Search for similar ideas
            similarity_results = await self.db.search_ideas_by_vector(
                query_embedding, 
                threshold=self.config.vector.similarity_threshold,
                limit=limit
            )
            
            # Filter by status if specified
            if status_filter:
                similarity_results = [
                    result for result in similarity_results 
                    if result.get("status") == status_filter
                ]
            
            # Format results
            formatted_results = []
            for result in similarity_results:
                formatted_result = {
                    "id": result["id"],
                    "title": result["title"],
                    "description": result["description"][:200] + "..." if len(result["description"]) > 200 else result["description"],
                    "submitter_name": result["submitter_name"],
                    "department": result["department"],
                    "status": result["status"],
                    "submission_date": result["submission_date"].isoformat() if result["submission_date"] else None,
                    "similarity_score": round(result["similarity"], 3),
                    "search_method": "semantic"
                }
                formatted_results.append(formatted_result)
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []
    
    async def _keyword_search(self, query: str, limit: int, 
                             status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Perform keyword-based search."""
        try:
            # Build keyword search query
            search_query = """
                SELECT 
                    id, title, description, submitter_name, department,
                    status, submission_date,
                    ts_rank(to_tsvector('english', title || ' ' || description), plainto_tsquery('english', $1)) as rank
                FROM ideas
                WHERE to_tsvector('english', title || ' ' || description) @@ plainto_tsquery('english', $1)
            """
            args = [query]
            
            if status_filter:
                search_query += " AND status = $2"
                args.append(status_filter)
            
            search_query += " ORDER BY rank DESC LIMIT $" + str(len(args) + 1)
            args.append(limit)
            
            results = await self.db.execute_query(search_query, *args)
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_result = {
                    "id": result["id"],
                    "title": result["title"],
                    "description": result["description"][:200] + "..." if len(result["description"]) > 200 else result["description"],
                    "submitter_name": result["submitter_name"],
                    "department": result["department"],
                    "status": result["status"],
                    "submission_date": result["submission_date"].isoformat() if result["submission_date"] else None,
                    "relevance_score": round(result["rank"], 3),
                    "search_method": "keyword"
                }
                formatted_results.append(formatted_result)
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error in keyword search: {e}")
            return []
    
    async def get_idea_details(self, idea_id: int) -> Dict[str, Any]:
        """Get detailed information about a specific idea."""
        try:
            logger.info(f"Getting details for idea ID: {idea_id}")
            
            idea = await self.db.get_idea_by_id(idea_id)
            
            if not idea:
                return {
                    "error": f"Idea with ID {idea_id} not found",
                    "idea_id": idea_id
                }
            
            # Format the idea details
            details = {
                "id": idea["id"],
                "title": idea["title"],
                "description": idea["description"],
                "submitter_info": {
                    "name": idea["submitter_name"],
                    "email": idea["submitter_email"],
                    "department": idea["department"]
                },
                "business_value": idea["business_value"],
                "technical_requirements": idea["technical_requirements"],
                "status": idea["status"],
                "admin_notes": idea["admin_notes"],
                "dates": {
                    "submitted": idea["submission_date"].isoformat() if idea["submission_date"] else None,
                    "last_updated": idea["last_updated"].isoformat() if idea["last_updated"] else None
                },
                "has_vector_embedding": idea["vector_embedding"] is not None
            }
            
            return details
            
        except Exception as e:
            logger.error(f"Error getting idea details: {e}")
            return {
                "error": str(e),
                "idea_id": idea_id
            }
    
    async def detect_duplicates(self, title: str, description: str, 
                               threshold: float = 0.8) -> Dict[str, Any]:
        """
        Detect duplicate or similar ideas based on title and description.
        
        Args:
            title: Title of the idea to check
            description: Description of the idea to check
            threshold: Similarity threshold (0.0-1.0)
            
        Returns:
            Dictionary containing potential duplicates and similarity scores
        """
        try:
            logger.info(f"Detecting duplicates for idea: '{title[:50]}...'")
            
            # Combine title and description for embedding
            content = f"{title} {description}"
            
            # Generate embedding
            content_embedding = await self.vector_tools.generate_embedding(content)
            
            # Search for similar ideas
            similar_ideas = await self.db.search_ideas_by_vector(
                content_embedding,
                threshold=threshold,
                limit=10
            )
            
            # Format duplicate detection results
            duplicates = []
            for similar in similar_ideas:
                duplicate_info = {
                    "id": similar["id"],
                    "title": similar["title"],
                    "description": similar["description"][:150] + "..." if len(similar["description"]) > 150 else similar["description"],
                    "submitter_name": similar["submitter_name"],
                    "department": similar["department"],
                    "status": similar["status"],
                    "similarity_score": round(similar["similarity"], 3),
                    "submission_date": similar["submission_date"].isoformat() if similar["submission_date"] else None
                }
                duplicates.append(duplicate_info)
            
            result = {
                "input_title": title,
                "input_description": description[:100] + "..." if len(description) > 100 else description,
                "threshold": threshold,
                "total_similar_ideas": len(duplicates),
                "potential_duplicates": duplicates,
                "has_duplicates": len(duplicates) > 0,
                "highest_similarity": max([d["similarity_score"] for d in duplicates]) if duplicates else 0.0,
                "timestamp": datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error detecting duplicates: {e}")
            return {
                "error": str(e),
                "input_title": title,
                "input_description": description[:100] + "..." if len(description) > 100 else description,
                "potential_duplicates": []
            }
    
    async def analyze_trends(self, time_period: str = "30days", 
                           category: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze trends in submitted ideas.
        
        Args:
            time_period: Time period for analysis ("7days", "30days", "90days", "1year")
            category: Optional category/department filter
            
        Returns:
            Dictionary containing trend analysis results
        """
        try:
            logger.info(f"Analyzing trends for period: {time_period}, category: {category}")
            
            # Parse time period
            days_map = {
                "7days": 7,
                "30days": 30,
                "90days": 90,
                "1year": 365
            }
            
            if time_period not in days_map:
                raise ValueError(f"Invalid time period: {time_period}")
            
            days = days_map[time_period]
            start_date = datetime.now() - timedelta(days=days)
            
            # Build base query
            base_query = """
                SELECT 
                    DATE_TRUNC('day', submission_date) as date,
                    COUNT(*) as count,
                    status,
                    department
                FROM ideas
                WHERE submission_date >= $1
            """
            args = [start_date]
            
            if category:
                base_query += " AND department = $2"
                args.append(category)
            
            # Get daily submission trends
            daily_query = base_query + """
                GROUP BY DATE_TRUNC('day', submission_date), status, department
                ORDER BY date DESC
            """
            daily_data = await self.db.execute_query(daily_query, *args)
            
            # Get overall stats for the period
            stats_query = """
                SELECT 
                    COUNT(*) as total_ideas,
                    COUNT(DISTINCT submitter_email) as unique_submitters,
                    COUNT(DISTINCT department) as departments_involved,
                    AVG(CASE WHEN status ILIKE '%approved%' THEN 1 ELSE 0 END) as approval_rate
                FROM ideas
                WHERE submission_date >= $1
            """
            if category:
                stats_query += " AND department = $2"
            
            stats = await self.db.execute_fetchrow(stats_query, *args)
            
            # Get top departments
            dept_query = """
                SELECT department, COUNT(*) as count
                FROM ideas
                WHERE submission_date >= $1
            """
            if category:
                dept_query += " AND department = $2"
            
            dept_query += """
                AND department IS NOT NULL
                GROUP BY department
                ORDER BY count DESC
                LIMIT 5
            """
            top_departments = await self.db.execute_query(dept_query, *args)
            
            # Process daily trends
            daily_trends = {}
            for row in daily_data:
                date_str = row["date"].strftime("%Y-%m-%d")
                if date_str not in daily_trends:
                    daily_trends[date_str] = {"total": 0, "by_status": {}}
                daily_trends[date_str]["total"] += row["count"]
                daily_trends[date_str]["by_status"][row["status"]] = row["count"]
            
            result = {
                "time_period": time_period,
                "category_filter": category,
                "analysis_date": datetime.now().isoformat(),
                "period_stats": {
                    "total_ideas": stats["total_ideas"],
                    "unique_submitters": stats["unique_submitters"],
                    "departments_involved": stats["departments_involved"],
                    "approval_rate": round(float(stats["approval_rate"]), 3) if stats["approval_rate"] else 0.0
                },
                "daily_trends": daily_trends,
                "top_departments": [
                    {"department": dept["department"], "idea_count": dept["count"]}
                    for dept in top_departments
                ]
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing trends: {e}")
            return {
                "error": str(e),
                "time_period": time_period,
                "category_filter": category
            }
