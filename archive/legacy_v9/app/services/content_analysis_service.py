# app/services/content_analysis_service.py
import logging
import re
import json
from typing import List, Dict, Any, Optional, Set
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.llm_config import get_llm
from app.database.models import Document

logger = logging.getLogger(__name__)

class ContentAnalysisService:
    """Service for AI-powered content analysis including tagging, summarization, and entity extraction."""
    
    # Predefined categories for automatic tagging
    CATEGORY_KEYWORDS = {
        "technology": ["software", "hardware", "computer", "programming", "code", "algorithm", "data", "digital", "tech", "system"],
        "science": ["research", "study", "experiment", "analysis", "theory", "hypothesis", "scientific", "method", "discovery"],
        "business": ["company", "market", "revenue", "profit", "strategy", "management", "finance", "sales", "customer"],
        "education": ["learning", "teaching", "student", "course", "curriculum", "academic", "school", "university", "knowledge"],
        "health": ["medical", "health", "patient", "treatment", "diagnosis", "therapy", "medicine", "clinical", "healthcare"],
        "legal": ["law", "legal", "contract", "agreement", "regulation", "compliance", "court", "attorney", "rights"],
        "finance": ["money", "investment", "banking", "financial", "budget", "cost", "price", "economic", "accounting"],
        "marketing": ["brand", "advertising", "promotion", "campaign", "social media", "content", "audience", "engagement"]
    }
    
    @staticmethod
    async def analyze_document_content(
        db: AsyncSession,
        document: Document,
        include_summary: bool = True,
        include_tags: bool = True,
        include_entities: bool = True
    ) -> Dict[str, Any]:
        """Perform comprehensive content analysis on a document."""
        try:
            analysis_result = {
                "document_id": document.id,
                "title": document.title,
                "content_length": len(document.content),
                "analysis_timestamp": None,
                "tags": [],
                "summary": "",
                "entities": {},
                "topics": [],
                "sentiment": "neutral",
                "readability_score": 0.0,
                "key_phrases": []
            }
            
            # Step 1: Extract automatic tags
            if include_tags:
                analysis_result["tags"] = await ContentAnalysisService._extract_automatic_tags(document.content)
            
            # Step 2: Generate summary using LLM
            if include_summary:
                analysis_result["summary"] = await ContentAnalysisService._generate_summary(document.content)

            # Step 3: Extract entities and topics
            if include_entities:
                entities_and_topics = await ContentAnalysisService._extract_entities_and_topics(document.content)
                analysis_result["entities"] = entities_and_topics["entities"]
                analysis_result["topics"] = entities_and_topics["topics"]
            
            # Step 4: Analyze sentiment
            analysis_result["sentiment"] = ContentAnalysisService._analyze_sentiment(document.content)
            
            # Step 5: Calculate readability score
            analysis_result["readability_score"] = ContentAnalysisService._calculate_readability(document.content)
            
            # Step 6: Extract key phrases
            analysis_result["key_phrases"] = ContentAnalysisService._extract_key_phrases(document.content)
            
            # Step 7: Stamp analysis time and update document with analysis results
            from datetime import datetime, timezone
            analysis_result["analysis_timestamp"] = datetime.now(timezone.utc).isoformat()
            await ContentAnalysisService._update_document_with_analysis(db, document, analysis_result)

            return analysis_result

        except Exception as e:
            logger.error(f"Content analysis failed for document {document.id}: {e}")
            return {
                "document_id": document.id,
                "error": str(e),
                "analysis_timestamp": None
            }
    
    @staticmethod
    async def _extract_automatic_tags(content: str) -> List[str]:
        """Extract automatic tags based on content analysis."""
        tags = set()
        content_lower = content.lower()
        
        # Category-based tagging
        for category, keywords in ContentAnalysisService.CATEGORY_KEYWORDS.items():
            keyword_count = sum(1 for keyword in keywords if keyword in content_lower)
            if keyword_count >= 2:  # Require at least 2 keywords for a category
                tags.add(category)
        
        # Extract technical terms (capitalized words, acronyms)
        technical_terms = re.findall(r'\b[A-Z]{2,}\b', content)
        for term in technical_terms[:5]:  # Limit to 5 technical terms
            if len(term) <= 10:  # Reasonable length
                tags.add(term.lower())
        
        # Extract programming languages and technologies
        tech_patterns = [
            r'\b(python|javascript|java|c\+\+|html|css|sql|react|angular|vue)\b',
            r'\b(api|rest|graphql|json|xml|yaml|docker|kubernetes)\b',
            r'\b(machine learning|ai|artificial intelligence|deep learning|neural network)\b'
        ]
        
        for pattern in tech_patterns:
            matches = re.findall(pattern, content_lower)
            for match in matches:
                tags.add(match.replace(' ', '_'))
        
        return list(tags)[:10]  # Limit to 10 tags
    
    @staticmethod
    async def _generate_summary(content: str) -> str:
        """Generate a summary using LLM capabilities."""
        try:
            if len(content) < 100:
                return content[:200] + "..." if len(content) > 200 else content

            # Try real LLM via llm_config
            try:
                llm = get_llm()
            except Exception as e:
                llm = None
                logger.warning(f"LLM not available, falling back to heuristic summary: {e}")

            if llm is not None:
                prompt = f"Please provide a concise summary of the following document in 2-3 sentences:\n\n{content[:2000]}\n\nSummary:"
                try:
                    # langchain chat models typically expose .invoke with a dict or string
                    result = llm.invoke(prompt)
                    if isinstance(result, str):
                        text = result
                    else:
                        # Try to access .content
                        text = getattr(result, "content", None) or str(result)
                    text = (text or "").strip()
                    if text:
                        return text
                except Exception as e:
                    logger.warning(f"LLM summarization failed: {e}")

            # Fallback: Extract first few sentences
            sentences = re.split(r'[.!?]+', content)
            summary_sentences = []
            char_count = 0

            for sentence in sentences:
                sentence = sentence.strip()
                if sentence and char_count + len(sentence) < 300:
                    summary_sentences.append(sentence)
                    char_count += len(sentence)
                else:
                    break

            return '. '.join(summary_sentences) + '.' if summary_sentences else content[:200] + "..."

        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            return content[:200] + "..." if len(content) > 200 else content

    @staticmethod
    async def _extract_entities_and_topics(content: str) -> Dict[str, Any]:
        """Extract entities and topics from content."""
        try:
            entities = {
                "persons": [],
                "organizations": [],
                "locations": [],
                "technologies": [],
                "concepts": []
            }
            
            # Simple regex-based entity extraction
            # Persons (capitalized names)
            person_pattern = r'\b[A-Z][a-z]+ [A-Z][a-z]+\b'
            persons = re.findall(person_pattern, content)
            entities["persons"] = list(set(persons))[:5]
            
            # Organizations (words ending with Inc, Corp, LLC, etc.)
            org_pattern = r'\b[A-Z][a-zA-Z\s]+(Inc|Corp|LLC|Ltd|Company|Corporation)\b'
            orgs = re.findall(org_pattern, content)
            entities["organizations"] = list(set(orgs))[:5]
            
            # Technologies (common tech terms)
            tech_terms = ["Python", "JavaScript", "React", "Docker", "Kubernetes", "AWS", "Azure", "API", "REST", "GraphQL"]
            found_tech = [term for term in tech_terms if term in content]
            entities["technologies"] = found_tech[:5]
            
            # Extract topics using keyword frequency
            words = re.findall(r'\b[a-zA-Z]{4,}\b', content.lower())
            word_freq = {}
            for word in words:
                if word not in ["this", "that", "with", "from", "they", "have", "been", "will", "were", "said"]:
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            # Get top topics
            topics = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
            topic_list = [topic[0] for topic in topics if topic[1] >= 2]
            
            return {
                "entities": entities,
                "topics": topic_list
            }
            
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            return {"entities": {}, "topics": []}
    
    @staticmethod
    def _analyze_sentiment(content: str) -> str:
        """Analyze sentiment of the content."""
        try:
            positive_words = ["good", "great", "excellent", "amazing", "wonderful", "fantastic", "positive", "success", "achieve", "improve"]
            negative_words = ["bad", "terrible", "awful", "horrible", "negative", "fail", "problem", "issue", "error", "difficult"]
            
            content_lower = content.lower()
            positive_count = sum(1 for word in positive_words if word in content_lower)
            negative_count = sum(1 for word in negative_words if word in content_lower)
            
            if positive_count > negative_count + 1:
                return "positive"
            elif negative_count > positive_count + 1:
                return "negative"
            else:
                return "neutral"
                
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return "neutral"
    
    @staticmethod
    def _calculate_readability(content: str) -> float:
        """Calculate a simple readability score."""
        try:
            sentences = len(re.split(r'[.!?]+', content))
            words = len(content.split())
            
            if sentences == 0 or words == 0:
                return 0.0
            
            avg_sentence_length = words / sentences
            
            # Simple readability score (lower is more readable)
            # Based on average sentence length
            if avg_sentence_length <= 15:
                return 0.9  # Very readable
            elif avg_sentence_length <= 20:
                return 0.7  # Readable
            elif avg_sentence_length <= 25:
                return 0.5  # Moderately readable
            else:
                return 0.3  # Difficult to read
                
        except Exception as e:
            logger.error(f"Readability calculation failed: {e}")
            return 0.5
    
    @staticmethod
    def _extract_key_phrases(content: str) -> List[str]:
        """Extract key phrases from content."""
        try:
            # Extract phrases with 2-4 words that appear multiple times
            phrases = re.findall(r'\b[a-zA-Z]+(?:\s+[a-zA-Z]+){1,3}\b', content)
            phrase_freq = {}
            
            for phrase in phrases:
                phrase_lower = phrase.lower()
                if len(phrase_lower) > 10 and len(phrase_lower) < 50:  # Reasonable phrase length
                    phrase_freq[phrase_lower] = phrase_freq.get(phrase_lower, 0) + 1
            
            # Get phrases that appear at least twice
            key_phrases = [phrase for phrase, freq in phrase_freq.items() if freq >= 2]
            return sorted(key_phrases, key=lambda x: phrase_freq[x], reverse=True)[:10]
            
        except Exception as e:
            logger.error(f"Key phrase extraction failed: {e}")
            return []
    
    @staticmethod
    async def _update_document_with_analysis(
        db: AsyncSession,
        document: Document,
        analysis_result: Dict[str, Any]
    ):
        """Update document with analysis results."""
        try:
            # Update document tags
            if analysis_result.get("tags"):
                existing_tags = document.tags or []
                new_tags = list(set(existing_tags + analysis_result["tags"]))
                document.tags = new_tags
            
            # Update document metadata with analysis results
            if not document.doc_metadata:
                document.doc_metadata = {}
            
            document.doc_metadata.update({
                "ai_analysis": {
                    "summary": analysis_result.get("summary", ""),
                    "entities": analysis_result.get("entities", {}),
                    "topics": analysis_result.get("topics", []),
                    "sentiment": analysis_result.get("sentiment", "neutral"),
                    "readability_score": analysis_result.get("readability_score", 0.0),
                    "key_phrases": analysis_result.get("key_phrases", []),
                    "analyzed_at": analysis_result.get("analysis_timestamp")
                }
            })
            
            await db.commit()
            logger.info(f"Updated document {document.id} with AI analysis results")
            
        except Exception as e:
            logger.error(f"Failed to update document with analysis: {e}")
            await db.rollback()
