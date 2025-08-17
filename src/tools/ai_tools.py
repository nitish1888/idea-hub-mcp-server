"""
AI Analysis Tools for MCP Server

This module provides AI-powered analysis tools for the Idea Hub platform,
including summary generation, feasibility assessment, and improvement suggestions.
"""

import logging
from typing import Any, Dict, List, Optional
import json
from datetime import datetime

try:
    import google.generativeai as genai
except ImportError:
    genai = None
    logging.warning("Google GenerativeAI not installed. AI tools will be limited.")

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import DatabaseConnection
from utils.config import MCPConfig

logger = logging.getLogger(__name__)


class AITools:
    """Tools for AI-powered analysis and generation."""
    
    def __init__(self, db: DatabaseConnection, config: MCPConfig):
        self.db = db
        self.config = config
        self.model = None
        self._initialize_ai_model()
    
    def _initialize_ai_model(self):
        """Initialize the AI model for generation tasks."""
        try:
            if not genai or not self.config.ai.google_api_key:
                logger.warning("Google AI not available. AI tools will be limited.")
                return
            
            genai.configure(api_key=self.config.ai.google_api_key)
            self.model = genai.GenerativeModel(self.config.ai.llm_model)
            logger.info("AI model initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize AI model: {e}")
            self.model = None
    
    async def generate_summary(self, idea_id: int, 
                             summary_type: str = "brief") -> Dict[str, Any]:
        """
        Generate AI summary of an idea.
        
        Args:
            idea_id: ID of the idea to summarize
            summary_type: Type of summary ("brief", "detailed", "technical", "business")
            
        Returns:
            Dictionary containing the generated summary
        """
        try:
            logger.info(f"Generating {summary_type} summary for idea ID: {idea_id}")
            
            # Get idea details
            idea = await self.db.get_idea_by_id(idea_id)
            if not idea:
                return {
                    "error": f"Idea with ID {idea_id} not found",
                    "idea_id": idea_id
                }
            
            if not self.model:
                return await self._fallback_summary(idea, summary_type)
            
            # Prepare prompt based on summary type
            prompt = self._get_summary_prompt(idea, summary_type)
            
            # Generate summary using AI
            try:
                response = self.model.generate_content(prompt)
                summary_text = response.text
            except Exception as e:
                logger.error(f"AI generation failed: {e}")
                return await self._fallback_summary(idea, summary_type)
            
            return {
                "idea_id": idea_id,
                "idea_title": idea["title"],
                "summary_type": summary_type,
                "summary": summary_text,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return {
                "error": str(e),
                "idea_id": idea_id,
                "summary_type": summary_type
            }
    
    async def assess_feasibility(self, idea_id: int) -> Dict[str, Any]:
        """
        Assess the technical and business feasibility of an idea.
        
        Args:
            idea_id: ID of the idea to assess
            
        Returns:
            Dictionary containing feasibility assessment
        """
        try:
            logger.info(f"Assessing feasibility for idea ID: {idea_id}")
            
            # Get idea details
            idea = await self.db.get_idea_by_id(idea_id)
            if not idea:
                return {
                    "error": f"Idea with ID {idea_id} not found",
                    "idea_id": idea_id
                }
            
            if not self.model:
                return await self._fallback_feasibility(idea)
            
            # Prepare feasibility assessment prompt
            prompt = self._get_feasibility_prompt(idea)
            
            # Generate assessment using AI
            try:
                response = self.model.generate_content(prompt)
                assessment_text = response.text
                
                # Parse the assessment to extract structured data
                assessment = self._parse_feasibility_assessment(assessment_text)
                
            except Exception as e:
                logger.error(f"AI feasibility assessment failed: {e}")
                return await self._fallback_feasibility(idea)
            
            return {
                "idea_id": idea_id,
                "idea_title": idea["title"],
                "feasibility_assessment": assessment,
                "raw_assessment": assessment_text,
                "assessed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error assessing feasibility: {e}")
            return {
                "error": str(e),
                "idea_id": idea_id
            }
    
    async def suggest_improvements(self, idea_id: int, 
                                 focus_area: str = "technical") -> Dict[str, Any]:
        """
        Suggest improvements for an idea.
        
        Args:
            idea_id: ID of the idea
            focus_area: Area to focus on ("technical", "business", "user_experience", "scalability")
            
        Returns:
            Dictionary containing improvement suggestions
        """
        try:
            logger.info(f"Generating {focus_area} improvements for idea ID: {idea_id}")
            
            # Get idea details
            idea = await self.db.get_idea_by_id(idea_id)
            if not idea:
                return {
                    "error": f"Idea with ID {idea_id} not found",
                    "idea_id": idea_id
                }
            
            if not self.model:
                return await self._fallback_improvements(idea, focus_area)
            
            # Prepare improvement prompt
            prompt = self._get_improvement_prompt(idea, focus_area)
            
            # Generate improvements using AI
            try:
                response = self.model.generate_content(prompt)
                improvements_text = response.text
                
                # Parse improvements into structured format
                improvements = self._parse_improvements(improvements_text)
                
            except Exception as e:
                logger.error(f"AI improvement generation failed: {e}")
                return await self._fallback_improvements(idea, focus_area)
            
            return {
                "idea_id": idea_id,
                "idea_title": idea["title"],
                "focus_area": focus_area,
                "improvements": improvements,
                "raw_suggestions": improvements_text,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating improvements: {e}")
            return {
                "error": str(e),
                "idea_id": idea_id,
                "focus_area": focus_area
            }
    
    async def analyze_sentiment(self, idea_id: int) -> Dict[str, Any]:
        """
        Analyze sentiment and tone of an idea.
        
        Args:
            idea_id: ID of the idea to analyze
            
        Returns:
            Dictionary containing sentiment analysis
        """
        try:
            logger.info(f"Analyzing sentiment for idea ID: {idea_id}")
            
            # Get idea details
            idea = await self.db.get_idea_by_id(idea_id)
            if not idea:
                return {
                    "error": f"Idea with ID {idea_id} not found",
                    "idea_id": idea_id
                }
            
            if not self.model:
                return await self._fallback_sentiment(idea)
            
            # Prepare sentiment analysis prompt
            prompt = self._get_sentiment_prompt(idea)
            
            # Generate sentiment analysis
            try:
                response = self.model.generate_content(prompt)
                sentiment_text = response.text
                
                # Parse sentiment analysis
                sentiment = self._parse_sentiment(sentiment_text)
                
            except Exception as e:
                logger.error(f"AI sentiment analysis failed: {e}")
                return await self._fallback_sentiment(idea)
            
            return {
                "idea_id": idea_id,
                "idea_title": idea["title"],
                "sentiment_analysis": sentiment,
                "raw_analysis": sentiment_text,
                "analyzed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return {
                "error": str(e),
                "idea_id": idea_id
            }
    
    def _get_summary_prompt(self, idea: Dict[str, Any], summary_type: str) -> str:
        """Generate prompt for summary creation."""
        base_info = f"""
        Title: {idea['title']}
        Description: {idea['description']}
        Business Value: {idea.get('business_value', 'Not specified')}
        Technical Requirements: {idea.get('technical_requirements', 'Not specified')}
        Department: {idea.get('department', 'Not specified')}
        """
        
        if summary_type == "brief":
            prompt = f"""
            Create a brief, 2-3 sentence summary of this idea:
            
            {base_info}
            
            Focus on the core concept and main benefits.
            """
        elif summary_type == "detailed":
            prompt = f"""
            Create a detailed summary of this idea including:
            1. Core concept and objectives
            2. Key benefits and business value
            3. Technical approach and requirements
            4. Potential challenges and considerations
            
            {base_info}
            """
        elif summary_type == "technical":
            prompt = f"""
            Create a technical summary focusing on:
            1. Technical architecture and approach
            2. Technology stack and requirements
            3. Implementation considerations
            4. Scalability and performance aspects
            
            {base_info}
            """
        elif summary_type == "business":
            prompt = f"""
            Create a business-focused summary including:
            1. Business value and ROI potential
            2. Market opportunity and competitive advantage
            3. Resource requirements and timeline
            4. Risk assessment and mitigation
            
            {base_info}
            """
        else:
            prompt = f"""
            Create a comprehensive summary of this idea:
            
            {base_info}
            """
        
        return prompt
    
    def _get_feasibility_prompt(self, idea: Dict[str, Any]) -> str:
        """Generate prompt for feasibility assessment."""
        return f"""
        Assess the feasibility of this idea across multiple dimensions:
        
        Title: {idea['title']}
        Description: {idea['description']}
        Business Value: {idea.get('business_value', 'Not specified')}
        Technical Requirements: {idea.get('technical_requirements', 'Not specified')}
        
        Please provide assessment in the following format:
        
        TECHNICAL FEASIBILITY (Score: 1-10):
        - Assessment and reasoning
        
        BUSINESS FEASIBILITY (Score: 1-10):
        - Assessment and reasoning
        
        RESOURCE FEASIBILITY (Score: 1-10):
        - Assessment and reasoning
        
        TIMELINE FEASIBILITY (Score: 1-10):
        - Assessment and reasoning
        
        OVERALL FEASIBILITY (Score: 1-10):
        - Summary and recommendation
        
        KEY RISKS:
        - List main risks
        
        SUCCESS FACTORS:
        - List key factors for success
        """
    
    def _get_improvement_prompt(self, idea: Dict[str, Any], focus_area: str) -> str:
        """Generate prompt for improvement suggestions."""
        focus_descriptions = {
            "technical": "technical implementation, architecture, and technology choices",
            "business": "business value, market potential, and commercial viability",
            "user_experience": "user experience, usability, and user satisfaction",
            "scalability": "scalability, performance, and growth potential"
        }
        
        focus_desc = focus_descriptions.get(focus_area, "overall improvement")
        
        return f"""
        Suggest specific improvements for this idea, focusing on {focus_desc}:
        
        Title: {idea['title']}
        Description: {idea['description']}
        Business Value: {idea.get('business_value', 'Not specified')}
        Technical Requirements: {idea.get('technical_requirements', 'Not specified')}
        
        Please provide 3-5 specific, actionable improvement suggestions.
        For each suggestion, include:
        1. What to improve
        2. Why it's important
        3. How to implement it
        4. Expected impact
        
        Format as a numbered list with clear, actionable items.
        """
    
    def _get_sentiment_prompt(self, idea: Dict[str, Any]) -> str:
        """Generate prompt for sentiment analysis."""
        return f"""
        Analyze the sentiment and tone of this idea submission:
        
        Title: {idea['title']}
        Description: {idea['description']}
        
        Please analyze:
        1. Overall sentiment (positive/neutral/negative)
        2. Confidence level of the submitter
        3. Clarity and specificity of the idea
        4. Enthusiasm and passion indicators
        5. Any concerns or hesitations expressed
        
        Provide scores (1-10) for each aspect and brief explanations.
        """
    
    def _parse_feasibility_assessment(self, assessment_text: str) -> Dict[str, Any]:
        """Parse feasibility assessment text into structured data."""
        try:
            # Extract scores using regex or simple parsing
            import re
            
            scores = {}
            score_pattern = r'(Score:\s*(\d+))'
            
            sections = ["TECHNICAL", "BUSINESS", "RESOURCE", "TIMELINE", "OVERALL"]
            
            for section in sections:
                section_match = re.search(rf'{section}.*?Score:\s*(\d+)', assessment_text, re.IGNORECASE | re.DOTALL)
                if section_match:
                    scores[section.lower() + "_score"] = int(section_match.group(1))
                else:
                    scores[section.lower() + "_score"] = 5  # Default neutral score
            
            return {
                "scores": scores,
                "average_score": round(sum(scores.values()) / len(scores), 1),
                "assessment_summary": assessment_text[:500] + "..." if len(assessment_text) > 500 else assessment_text
            }
            
        except Exception as e:
            logger.error(f"Error parsing feasibility assessment: {e}")
            return {
                "scores": {"overall_score": 5},
                "average_score": 5.0,
                "assessment_summary": assessment_text[:500] + "..." if len(assessment_text) > 500 else assessment_text
            }
    
    def _parse_improvements(self, improvements_text: str) -> List[Dict[str, str]]:
        """Parse improvement suggestions into structured format."""
        try:
            # Split by numbered items
            import re
            
            # Find numbered items (1., 2., etc.)
            items = re.split(r'\n\s*\d+\.', improvements_text)
            
            improvements = []
            for i, item in enumerate(items[1:], 1):  # Skip first empty split
                if item.strip():
                    improvements.append({
                        "id": i,
                        "suggestion": item.strip(),
                        "priority": "medium"  # Default priority
                    })
            
            # If no numbered items found, treat as single improvement
            if not improvements and improvements_text.strip():
                improvements.append({
                    "id": 1,
                    "suggestion": improvements_text.strip(),
                    "priority": "medium"
                })
            
            return improvements
            
        except Exception as e:
            logger.error(f"Error parsing improvements: {e}")
            return [{"id": 1, "suggestion": improvements_text[:200] + "...", "priority": "medium"}]
    
    def _parse_sentiment(self, sentiment_text: str) -> Dict[str, Any]:
        """Parse sentiment analysis into structured data."""
        try:
            # Extract numerical scores if present
            import re
            
            scores = {}
            score_matches = re.findall(r'(\w+).*?(\d+)/10', sentiment_text)
            
            for match in score_matches:
                aspect, score = match
                scores[aspect.lower()] = int(score)
            
            # Determine overall sentiment
            overall_sentiment = "neutral"
            if "positive" in sentiment_text.lower():
                overall_sentiment = "positive"
            elif "negative" in sentiment_text.lower():
                overall_sentiment = "negative"
            
            return {
                "overall_sentiment": overall_sentiment,
                "scores": scores,
                "analysis_summary": sentiment_text[:300] + "..." if len(sentiment_text) > 300 else sentiment_text
            }
            
        except Exception as e:
            logger.error(f"Error parsing sentiment: {e}")
            return {
                "overall_sentiment": "neutral",
                "scores": {},
                "analysis_summary": sentiment_text[:300] + "..." if len(sentiment_text) > 300 else sentiment_text
            }
    
    async def _fallback_summary(self, idea: Dict[str, Any], summary_type: str) -> Dict[str, Any]:
        """Fallback summary when AI is not available."""
        return {
            "idea_id": idea["id"],
            "idea_title": idea["title"],
            "summary_type": summary_type,
            "summary": f"Summary for '{idea['title']}': {idea['description'][:200]}...",
            "generated_at": datetime.now().isoformat(),
            "fallback": True
        }
    
    async def _fallback_feasibility(self, idea: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback feasibility assessment when AI is not available."""
        return {
            "idea_id": idea["id"],
            "idea_title": idea["title"],
            "feasibility_assessment": {
                "scores": {"overall_score": 5},
                "average_score": 5.0,
                "assessment_summary": "AI assessment not available. Manual review required."
            },
            "assessed_at": datetime.now().isoformat(),
            "fallback": True
        }
    
    async def _fallback_improvements(self, idea: Dict[str, Any], focus_area: str) -> Dict[str, Any]:
        """Fallback improvements when AI is not available."""
        return {
            "idea_id": idea["id"],
            "idea_title": idea["title"],
            "focus_area": focus_area,
            "improvements": [
                {
                    "id": 1,
                    "suggestion": "Consider conducting stakeholder interviews to validate requirements",
                    "priority": "high"
                },
                {
                    "id": 2,
                    "suggestion": "Develop a detailed technical specification document",
                    "priority": "medium"
                }
            ],
            "generated_at": datetime.now().isoformat(),
            "fallback": True
        }
    
    async def _fallback_sentiment(self, idea: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback sentiment analysis when AI is not available."""
        return {
            "idea_id": idea["id"],
            "idea_title": idea["title"],
            "sentiment_analysis": {
                "overall_sentiment": "neutral",
                "scores": {},
                "analysis_summary": "Sentiment analysis not available. AI model required."
            },
            "analyzed_at": datetime.now().isoformat(),
            "fallback": True
        }
