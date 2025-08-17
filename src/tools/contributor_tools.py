"""
Contributor Management Tools for MCP Server

This module provides tools for managing contributors in the Idea Hub platform,
including searching by skills, matching to ideas, and analyzing availability.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
import re
from datetime import datetime

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import DatabaseConnection
from utils.config import MCPConfig

logger = logging.getLogger(__name__)


class ContributorTools:
    """Tools for contributor management operations."""
    
    def __init__(self, db: DatabaseConnection, config: MCPConfig):
        self.db = db
        self.config = config
    
    async def search_contributors(self, skills: Optional[List[str]] = None,
                                availability: Optional[str] = None,
                                experience_level: Optional[str] = None,
                                department: Optional[str] = None,
                                limit: int = 20) -> Dict[str, Any]:
        """
        Search for contributors based on various criteria.
        
        Args:
            skills: List of required skills
            availability: Required availability (e.g., "full-time", "part-time", "10+ hours")
            experience_level: Required experience level
            department: Department filter
            limit: Maximum number of results
            
        Returns:
            Dictionary containing search results and metadata
        """
        try:
            logger.info(f"Searching contributors: skills={skills}, availability={availability}")
            
            # Build the search query
            query = """
                SELECT 
                    id, name, email, department, skills, experience_level,
                    hours_available, preferred_project_types, bio
                FROM contributors
                WHERE 1=1
            """
            args = []
            conditions = []
            
            # Add skill filters
            if skills:
                skill_conditions = []
                for skill in skills:
                    args.append(f"%{skill.lower()}%")
                    skill_conditions.append(f"LOWER(skills) LIKE ${len(args)}")
                
                if skill_conditions:
                    conditions.append(f"({' OR '.join(skill_conditions)})")
            
            # Add availability filter
            if availability:
                args.append(f"%{availability.lower()}%")
                conditions.append(f"LOWER(hours_available) LIKE ${len(args)}")
            
            # Add experience level filter
            if experience_level:
                args.append(experience_level.lower())
                conditions.append(f"LOWER(experience_level) = ${len(args)}")
            
            # Add department filter
            if department:
                args.append(department.lower())
                conditions.append(f"LOWER(department) = ${len(args)}")
            
            # Combine conditions
            if conditions:
                query += " AND " + " AND ".join(conditions)
            
            # Add ordering and limit
            query += f" ORDER BY name LIMIT ${len(args) + 1}"
            args.append(limit)
            
            # Execute query
            results = await self.db.execute_query(query, *args)
            
            # Format results
            formatted_results = []
            for contributor in results:
                # Parse skills
                skills_list = self._parse_skills(contributor.get("skills", ""))
                
                # Calculate skill match score if skills were provided in search
                skill_match_score = 0.0
                if skills:
                    skill_match_score = self._calculate_skill_match(skills, skills_list)
                
                formatted_contributor = {
                    "id": contributor["id"],
                    "name": contributor["name"],
                    "email": contributor["email"],
                    "department": contributor["department"],
                    "skills": skills_list,
                    "experience_level": contributor["experience_level"],
                    "hours_available": contributor["hours_available"],
                    "preferred_project_types": contributor.get("preferred_project_types", ""),
                    "bio": contributor.get("bio", "")[:200] + "..." if contributor.get("bio", "") and len(contributor.get("bio", "")) > 200 else contributor.get("bio", ""),
                    "skill_match_score": round(skill_match_score, 3) if skills else None
                }
                formatted_results.append(formatted_contributor)
            
            # Sort by skill match score if applicable
            if skills:
                formatted_results.sort(key=lambda x: x["skill_match_score"], reverse=True)
            
            return {
                "search_criteria": {
                    "skills": skills,
                    "availability": availability,
                    "experience_level": experience_level,
                    "department": department
                },
                "total_results": len(formatted_results),
                "results": formatted_results,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error searching contributors: {e}")
            return {
                "error": str(e),
                "search_criteria": {
                    "skills": skills,
                    "availability": availability,
                    "experience_level": experience_level,
                    "department": department
                },
                "results": []
            }
    
    async def match_to_idea(self, idea_id: int, 
                           required_skills: Optional[List[str]] = None,
                           max_contributors: int = 5) -> Dict[str, Any]:
        """
        Find contributors that match an idea's requirements.
        
        Args:
            idea_id: ID of the idea to match contributors to
            required_skills: List of required skills (if not provided, will be extracted from idea)
            max_contributors: Maximum number of contributors to return
            
        Returns:
            Dictionary containing matched contributors and scores
        """
        try:
            logger.info(f"Matching contributors to idea ID: {idea_id}")
            
            # Get idea details
            idea = await self.db.get_idea_by_id(idea_id)
            if not idea:
                return {
                    "error": f"Idea with ID {idea_id} not found",
                    "idea_id": idea_id
                }
            
            # Extract skills from idea if not provided
            if not required_skills:
                required_skills = self._extract_skills_from_idea(idea)
            
            if not required_skills:
                return {
                    "error": "No skills could be determined for this idea",
                    "idea_id": idea_id,
                    "idea_title": idea["title"]
                }
            
            # Search for contributors with matching skills
            search_result = await self.search_contributors(
                skills=required_skills,
                limit=max_contributors * 3  # Get more to allow for better filtering
            )
            
            if "error" in search_result:
                return search_result
            
            contributors = search_result["results"]
            
            # Enhanced matching with additional scoring
            matched_contributors = []
            for contributor in contributors[:max_contributors]:
                # Calculate comprehensive match score
                match_score = self._calculate_comprehensive_match(
                    contributor, idea, required_skills
                )
                
                contributor_match = {
                    "contributor": contributor,
                    "match_score": round(match_score, 3),
                    "match_reasons": self._get_match_reasons(contributor, idea, required_skills)
                }
                matched_contributors.append(contributor_match)
            
            # Sort by match score
            matched_contributors.sort(key=lambda x: x["match_score"], reverse=True)
            
            return {
                "idea_id": idea_id,
                "idea_title": idea["title"],
                "required_skills": required_skills,
                "total_matches": len(matched_contributors),
                "matched_contributors": matched_contributors,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error matching contributors to idea: {e}")
            return {
                "error": str(e),
                "idea_id": idea_id
            }
    
    async def get_contributor_details(self, contributor_id: int) -> Dict[str, Any]:
        """Get detailed information about a specific contributor."""
        try:
            query = """
                SELECT 
                    id, name, email, department, skills, experience_level,
                    hours_available, preferred_project_types, bio
                FROM contributors
                WHERE id = $1
            """
            
            contributor = await self.db.execute_fetchrow(query, contributor_id)
            
            if not contributor:
                return {
                    "error": f"Contributor with ID {contributor_id} not found",
                    "contributor_id": contributor_id
                }
            
            # Format the contributor details
            details = {
                "id": contributor["id"],
                "name": contributor["name"],
                "email": contributor["email"],
                "department": contributor["department"],
                "skills": self._parse_skills(contributor.get("skills", "")),
                "experience_level": contributor["experience_level"],
                "hours_available": contributor["hours_available"],
                "preferred_project_types": contributor.get("preferred_project_types", ""),
                "bio": contributor.get("bio", "")
            }
            
            return details
            
        except Exception as e:
            logger.error(f"Error getting contributor details: {e}")
            return {
                "error": str(e),
                "contributor_id": contributor_id
            }
    
    async def analyze_skill_gaps(self, required_skills: List[str]) -> Dict[str, Any]:
        """
        Analyze skill gaps in the contributor pool.
        
        Args:
            required_skills: List of skills to analyze
            
        Returns:
            Dictionary containing skill gap analysis
        """
        try:
            logger.info(f"Analyzing skill gaps for: {required_skills}")
            
            # Get all contributors
            all_contributors = await self.db.get_contributors()
            
            if not all_contributors:
                return {
                    "error": "No contributors found in database",
                    "required_skills": required_skills
                }
            
            skill_analysis = {}
            
            for skill in required_skills:
                # Count contributors with this skill
                contributors_with_skill = 0
                skill_levels = {"junior": 0, "mid-level": 0, "senior": 0, "expert": 0}
                
                for contributor in all_contributors:
                    contributor_skills = self._parse_skills(contributor.get("skills", ""))
                    
                    if any(skill.lower() in cs.lower() for cs in contributor_skills):
                        contributors_with_skill += 1
                        
                        # Count by experience level
                        exp_level = contributor.get("experience_level", "").lower()
                        if exp_level in skill_levels:
                            skill_levels[exp_level] += 1
                
                # Calculate skill availability
                total_contributors = len(all_contributors)
                availability_percentage = (contributors_with_skill / total_contributors) * 100 if total_contributors > 0 else 0
                
                skill_analysis[skill] = {
                    "contributors_with_skill": contributors_with_skill,
                    "total_contributors": total_contributors,
                    "availability_percentage": round(availability_percentage, 2),
                    "by_experience_level": skill_levels,
                    "gap_severity": self._assess_gap_severity(availability_percentage)
                }
            
            # Overall gap assessment
            overall_gap = sum(
                1 for skill_data in skill_analysis.values()
                if skill_data["gap_severity"] in ["high", "critical"]
            )
            
            return {
                "required_skills": required_skills,
                "total_contributors_analyzed": len(all_contributors),
                "skill_analysis": skill_analysis,
                "overall_gap_assessment": {
                    "skills_with_gaps": overall_gap,
                    "total_skills_analyzed": len(required_skills),
                    "gap_percentage": round((overall_gap / len(required_skills)) * 100, 2) if required_skills else 0
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing skill gaps: {e}")
            return {
                "error": str(e),
                "required_skills": required_skills
            }
    
    def _parse_skills(self, skills_string: str) -> List[str]:
        """Parse skills from a string into a list."""
        if not skills_string:
            return []
        
        # Split by common delimiters and clean up
        skills = re.split(r'[,;|]+', skills_string)
        return [skill.strip() for skill in skills if skill.strip()]
    
    def _calculate_skill_match(self, required_skills: List[str], 
                              contributor_skills: List[str]) -> float:
        """Calculate skill match score between required and contributor skills."""
        if not required_skills or not contributor_skills:
            return 0.0
        
        required_lower = [skill.lower() for skill in required_skills]
        contributor_lower = [skill.lower() for skill in contributor_skills]
        
        matches = 0
        for req_skill in required_lower:
            for contrib_skill in contributor_lower:
                if req_skill in contrib_skill or contrib_skill in req_skill:
                    matches += 1
                    break
        
        return matches / len(required_skills)
    
    def _extract_skills_from_idea(self, idea: Dict[str, Any]) -> List[str]:
        """Extract potential skills from idea description and technical requirements."""
        skills = []
        
        # Common technical skills to look for
        common_skills = [
            "python", "javascript", "java", "react", "angular", "vue", "node.js",
            "docker", "kubernetes", "aws", "azure", "gcp", "terraform",
            "machine learning", "ai", "data science", "sql", "postgresql", "mongodb",
            "redis", "elasticsearch", "kafka", "microservices", "api", "rest",
            "graphql", "frontend", "backend", "full-stack", "devops", "security",
            "mobile", "ios", "android", "flutter", "react native", "testing",
            "automation", "ci/cd", "jenkins", "github actions", "linux", "windows"
        ]
        
        # Combine title, description, and technical requirements
        text_to_analyze = f"{idea.get('title', '')} {idea.get('description', '')} {idea.get('technical_requirements', '')}"
        text_lower = text_to_analyze.lower()
        
        # Find matching skills
        for skill in common_skills:
            if skill in text_lower:
                skills.append(skill)
        
        return skills[:10]  # Limit to top 10 most relevant skills
    
    def _calculate_comprehensive_match(self, contributor: Dict[str, Any], 
                                     idea: Dict[str, Any], 
                                     required_skills: List[str]) -> float:
        """Calculate a comprehensive match score considering multiple factors."""
        score = 0.0
        
        # Skill match (60% weight)
        skill_score = contributor.get("skill_match_score", 0.0)
        score += skill_score * 0.6
        
        # Experience level match (20% weight)
        exp_score = self._calculate_experience_match(
            contributor.get("experience_level", ""),
            idea.get("technical_requirements", "")
        )
        score += exp_score * 0.2
        
        # Department relevance (10% weight)
        dept_score = self._calculate_department_match(
            contributor.get("department", ""),
            idea.get("department", "")
        )
        score += dept_score * 0.1
        
        # Availability match (10% weight)
        avail_score = self._calculate_availability_match(
            contributor.get("hours_available", "")
        )
        score += avail_score * 0.1
        
        return min(1.0, score)  # Cap at 1.0
    
    def _calculate_experience_match(self, contributor_exp: str, tech_requirements: str) -> float:
        """Calculate experience level match score."""
        if not contributor_exp or not tech_requirements:
            return 0.5  # Neutral score
        
        exp_lower = contributor_exp.lower()
        req_lower = tech_requirements.lower()
        
        # Simple heuristics
        if "senior" in exp_lower and ("complex" in req_lower or "advanced" in req_lower):
            return 1.0
        elif "junior" in exp_lower and ("simple" in req_lower or "basic" in req_lower):
            return 1.0
        elif "mid" in exp_lower:
            return 0.8
        
        return 0.5
    
    def _calculate_department_match(self, contributor_dept: str, idea_dept: str) -> float:
        """Calculate department match score."""
        if not contributor_dept or not idea_dept:
            return 0.5
        
        return 1.0 if contributor_dept.lower() == idea_dept.lower() else 0.3
    
    def _calculate_availability_match(self, hours_available: str) -> float:
        """Calculate availability match score."""
        if not hours_available:
            return 0.5
        
        hours_lower = hours_available.lower()
        
        # Extract numeric values
        numbers = re.findall(r'\d+', hours_available)
        
        if numbers:
            avg_hours = sum(int(n) for n in numbers) / len(numbers)
            if avg_hours >= 20:
                return 1.0
            elif avg_hours >= 10:
                return 0.8
            elif avg_hours >= 5:
                return 0.6
            else:
                return 0.4
        
        # Fallback to text analysis
        if "full" in hours_lower:
            return 1.0
        elif "part" in hours_lower:
            return 0.7
        
        return 0.5
    
    def _get_match_reasons(self, contributor: Dict[str, Any], 
                          idea: Dict[str, Any], 
                          required_skills: List[str]) -> List[str]:
        """Get reasons why this contributor matches the idea."""
        reasons = []
        
        # Skill matches
        contributor_skills = contributor.get("skills", [])
        skill_matches = []
        for req_skill in required_skills:
            for contrib_skill in contributor_skills:
                if req_skill.lower() in contrib_skill.lower():
                    skill_matches.append(contrib_skill)
                    break
        
        if skill_matches:
            reasons.append(f"Has relevant skills: {', '.join(skill_matches[:3])}")
        
        # Experience level
        if contributor.get("experience_level"):
            reasons.append(f"Experience level: {contributor['experience_level']}")
        
        # Department match
        if (contributor.get("department") and idea.get("department") and 
            contributor["department"].lower() == idea["department"].lower()):
            reasons.append(f"Same department: {contributor['department']}")
        
        # Availability
        if contributor.get("hours_available"):
            reasons.append(f"Availability: {contributor['hours_available']}")
        
        return reasons
    
    def _assess_gap_severity(self, availability_percentage: float) -> str:
        """Assess the severity of a skill gap."""
        if availability_percentage >= 50:
            return "low"
        elif availability_percentage >= 30:
            return "medium"
        elif availability_percentage >= 10:
            return "high"
        else:
            return "critical"
