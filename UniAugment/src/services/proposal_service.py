"""
Project Proposal Generation Service using Google Gemini API.

This service analyzes uploaded documents and generates comprehensive project proposals
using Google's Gemini AI for deep research and analysis.
"""

import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.models import Document

logger = logging.getLogger(__name__)


class ProposalService:
    """Service for generating project proposals using Google Gemini."""
    
    def __init__(self):
        """Initialize the proposal service with Gemini API."""
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
        self.gemini_available = False
        self.genai = None
        
        # Try to import and configure Gemini
        try:
            import google.generativeai as genai
            if self.api_key:
                genai.configure(api_key=self.api_key)
                self.genai = genai
                self.gemini_available = True
                logger.info(f"Gemini API initialized successfully with model: {self.model_name}")
            else:
                logger.warning("GEMINI_API_KEY not found in environment variables")
        except ImportError:
            logger.warning("google-generativeai package not installed. Install with: pip install google-generativeai")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini API: {e}")
    
    async def generate_proposal(
        self,
        db: AsyncSession,
        user_id: str,
        proposal_type: str = "general",
        focus_areas: Optional[List[str]] = None,
        additional_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive project proposal based on user's uploaded documents.
        
        Args:
            db: Database session
            user_id: User ID to fetch documents for
            proposal_type: Type of proposal (general, technical, business, research)
            focus_areas: Specific areas to focus on in the analysis
            additional_context: Additional context or requirements for the proposal
            
        Returns:
            Dictionary containing the generated proposal and metadata
        """
        if not self.gemini_available:
            return {
                "success": False,
                "error": "Gemini API not available. Please configure GEMINI_API_KEY.",
                "proposal": None
            }
        
        try:
            # Fetch all active documents for the user
            result = await db.execute(
                select(Document)
                .where(Document.user_id == user_id)
                .where(Document.is_active == True)
                .order_by(Document.created_at.desc())
            )
            documents = result.scalars().all()
            
            if not documents:
                return {
                    "success": False,
                    "error": "No documents found. Please upload documents first.",
                    "proposal": None
                }
            
            # Prepare document summaries for Gemini
            doc_summaries = []
            total_chars = 0
            max_chars = 1_000_000  # Gemini 1.5 Pro has 1M token context
            
            for doc in documents:
                # Truncate very long documents to fit in context
                content = doc.content[:50000] if len(doc.content) > 50000 else doc.content
                doc_summary = {
                    "title": doc.title,
                    "content_type": doc.content_type,
                    "content": content,
                    "created_at": doc.created_at.isoformat(),
                    "metadata": doc.doc_metadata or {}
                }
                doc_summaries.append(doc_summary)
                total_chars += len(content)
                
                if total_chars > max_chars:
                    logger.warning(f"Reached context limit, using {len(doc_summaries)} documents")
                    break
            
            # Generate the proposal using Gemini
            proposal_content = await self._generate_with_gemini(
                documents=doc_summaries,
                proposal_type=proposal_type,
                focus_areas=focus_areas or [],
                additional_context=additional_context
            )
            
            return {
                "success": True,
                "proposal": proposal_content,
                "metadata": {
                    "documents_analyzed": len(doc_summaries),
                    "total_documents": len(documents),
                    "proposal_type": proposal_type,
                    "generated_at": datetime.utcnow().isoformat(),
                    "model_used": self.model_name
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating proposal: {e}")
            return {
                "success": False,
                "error": f"Failed to generate proposal: {str(e)}",
                "proposal": None
            }
    
    async def _generate_with_gemini(
        self,
        documents: List[Dict[str, Any]],
        proposal_type: str,
        focus_areas: List[str],
        additional_context: Optional[str]
    ) -> Dict[str, Any]:
        """Generate proposal content using Gemini API."""
        
        # Build the prompt based on proposal type
        prompt = self._build_proposal_prompt(
            documents=documents,
            proposal_type=proposal_type,
            focus_areas=focus_areas,
            additional_context=additional_context
        )
        
        # Call Gemini API
        model = self.genai.GenerativeModel(self.model_name)
        
        # Configure generation parameters for thorough analysis
        generation_config = {
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
        }
        
        response = model.generate_content(
            prompt,
            generation_config=generation_config
        )
        
        # Parse the response into structured sections
        proposal_text = response.text
        
        # Extract sections from the response
        sections = self._parse_proposal_sections(proposal_text)
        
        return {
            "full_text": proposal_text,
            "sections": sections,
            "word_count": len(proposal_text.split()),
            "char_count": len(proposal_text)
        }
    
    def _build_proposal_prompt(
        self,
        documents: List[Dict[str, Any]],
        proposal_type: str,
        focus_areas: List[str],
        additional_context: Optional[str]
    ) -> str:
        """Build a comprehensive prompt for Gemini to generate the proposal."""
        
        # Document summaries
        doc_context = "\n\n".join([
            f"### Document: {doc['title']}\n"
            f"Type: {doc['content_type']}\n"
            f"Created: {doc['created_at']}\n"
            f"Content:\n{doc['content']}\n"
            for doc in documents
        ])
        
        # Base prompt template
        base_prompt = f"""You are an expert project analyst and proposal writer. You have been provided with {len(documents)} documents to analyze and create a comprehensive project proposal.

**DOCUMENTS TO ANALYZE:**
{doc_context}

**PROPOSAL TYPE:** {proposal_type.upper()}

**YOUR TASK:**
Conduct a deep analysis of all provided documents and generate a comprehensive, professional project proposal. Your analysis should be thorough, insightful, and actionable.

**REQUIRED SECTIONS:**
1. **Executive Summary** - High-level overview of the project and key recommendations
2. **Project Overview** - Detailed description of the project scope and objectives
3. **Document Analysis** - Key findings, themes, and insights from the analyzed documents
4. **Recommendations** - Specific, actionable recommendations based on the analysis
5. **Implementation Plan** - Proposed timeline, milestones, and approach
6. **Resource Requirements** - Team, budget, tools, and other resources needed
7. **Risk Analysis** - Potential risks and mitigation strategies
8. **Success Metrics** - How to measure project success
9. **Conclusion** - Summary and next steps

"""
        
        # Add focus areas if specified
        if focus_areas:
            focus_text = ", ".join(focus_areas)
            base_prompt += f"\n**FOCUS AREAS:** Pay special attention to: {focus_text}\n"
        
        # Add additional context if provided
        if additional_context:
            base_prompt += f"\n**ADDITIONAL CONTEXT:**\n{additional_context}\n"
        
        # Add formatting instructions
        base_prompt += """
**FORMATTING INSTRUCTIONS:**
- Use clear markdown formatting with headers (##, ###)
- Include bullet points and numbered lists where appropriate
- Be specific and cite information from the documents
- Provide concrete examples and data points
- Make the proposal actionable and professional
- Aim for 2000-3000 words for comprehensive coverage

Begin your analysis and proposal generation now:
"""
        
        return base_prompt
    
    def _parse_proposal_sections(self, proposal_text: str) -> Dict[str, str]:
        """Parse the proposal text into structured sections."""
        sections = {}
        current_section = "introduction"
        current_content = []
        
        lines = proposal_text.split('\n')
        
        for line in lines:
            # Check if line is a section header (## or ###)
            if line.strip().startswith('##'):
                # Save previous section
                if current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                
                # Start new section
                section_name = line.strip('#').strip().lower().replace(' ', '_')
                current_section = section_name
                current_content = []
            else:
                current_content.append(line)
        
        # Save last section
        if current_content:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return sections


# Global instance
proposal_service = ProposalService()

