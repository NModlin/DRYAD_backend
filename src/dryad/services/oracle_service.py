"""
Oracle Service

Platform-agnostic service for oracle (LLM) operations.
Ported from TypeScript services/oracle-service-wrapper.ts
"""

import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from dryad.database.models.dialogue import Dialogue
from dryad.database.models.dialogue_message import DialogueMessage, MessageRole
from dryad.database.models.branch import Branch
from dryad.database.models.vessel import Vessel
from dryad.schemas.dialogue_schemas import (
    ConsultationRequest, ConsultationResponse, ProcessResponseRequest,
    ProcessResponseResult, DialogueResponse, ProviderInfo, ParsedWisdom
)
from dryad.core.exceptions import DryadError, DryadErrorCode, NotFoundError, wrap_error
from dryad.core.llm_config import create_llm
from dryad.core.llm_error_handler import llm_error_handler
from dryad.core.logging_config import get_logger

logger = get_logger(__name__)


class OracleService:
    """Platform-agnostic Oracle Service for LLM consultation operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm = create_llm()  # Use DRYAD.AI's LLM system
        logger.info("OracleService initialized")
    
    async def get_providers(self) -> List[ProviderInfo]:
        """
        Get all available oracle providers.
        
        Returns:
            List of provider information
        """
        try:
            logger.debug("Getting all oracle providers")
            
            # For now, return the configured LLM provider
            # TODO: Implement provider registry
            providers = [
                ProviderInfo(
                    id="llamacpp",
                    name="LlamaCpp",
                    description="Local LlamaCpp provider",
                    enabled=True
                ),
                ProviderInfo(
                    id="openai",
                    name="OpenAI",
                    description="OpenAI GPT models",
                    enabled=False
                ),
                ProviderInfo(
                    id="ollama",
                    name="Ollama",
                    description="Local Ollama provider",
                    enabled=False
                )
            ]
            
            logger.info(f"Retrieved {len(providers)} oracle providers")
            return providers
            
        except Exception as e:
            logger.error(f"Failed to get providers: {e}")
            raise wrap_error(
                e, DryadErrorCode.ORACLE_PROVIDER_NOT_FOUND,
                "Failed to get providers"
            )
    
    async def get_provider(self, provider_id: str) -> Optional[ProviderInfo]:
        """
        Get a specific provider by ID.
        
        Args:
            provider_id: Provider ID
            
        Returns:
            Provider information or None if not found
        """
        try:
            logger.debug(f"Getting provider: {provider_id}")
            
            providers = await self.get_providers()
            provider = next((p for p in providers if p.id == provider_id), None)
            
            if provider:
                logger.debug(f"Provider retrieved: {provider_id}")
            else:
                logger.warning(f"Provider not found: {provider_id}")
            
            return provider
            
        except Exception as e:
            logger.error(f"Failed to get provider {provider_id}: {e}")
            raise wrap_error(
                e, DryadErrorCode.ORACLE_PROVIDER_NOT_FOUND,
                f"Failed to get provider: {provider_id}",
                {"provider_id": provider_id}
            )
    
    async def prepare_consultation(self, request: ConsultationRequest) -> ConsultationResponse:
        """
        Prepare a consultation with an oracle.
        
        Args:
            request: Consultation request
            
        Returns:
            Consultation response with formatted prompt
        """
        try:
            logger.debug(f"Preparing consultation for branch {request.branch_id}")
            
            # Validate branch exists
            branch_stmt = select(Branch).where(Branch.id == request.branch_id)
            branch_result = await self.db.execute(branch_stmt)
            branch = branch_result.scalar_one_or_none()
            
            if not branch:
                raise NotFoundError("Branch", request.branch_id)
            
            # Get vessel for context
            vessel_stmt = select(Vessel).where(Vessel.branch_id == request.branch_id)
            vessel_result = await self.db.execute(vessel_stmt)
            vessel = vessel_result.scalar_one_or_none()
            
            if not vessel:
                raise NotFoundError("Vessel", f"for branch {request.branch_id}")
            
            # Build context-aware prompt
            formatted_prompt = await self._build_consultation_prompt(
                vessel, request.query, request.provider_id
            )
            
            response = ConsultationResponse(
                formatted_prompt=formatted_prompt,
                metadata={
                    "provider": request.provider_id,
                    "branch_id": request.branch_id,
                    "vessel_id": vessel.id,
                    "timestamp": datetime.utcnow()
                }
            )
            
            logger.info(f"Consultation prepared for branch {request.branch_id}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to prepare consultation: {e}")
            raise wrap_error(
                e, DryadErrorCode.ORACLE_CONSULTATION_FAILED,
                "Failed to prepare consultation",
                {"branch_id": request.branch_id, "provider_id": request.provider_id}
            )
    
    async def consult_oracle(self, request: ConsultationRequest) -> ProcessResponseResult:
        """
        Consult oracle and process response with comprehensive error handling.

        Args:
            request: Consultation request

        Returns:
            Process response result
        """
        try:
            logger.debug(f"Consulting oracle for branch {request.branch_id}")

            # Prepare consultation
            consultation = await self.prepare_consultation(request)

            # Define fallback response
            fallback_response = (
                f"I understand your query: '{request.query}'. "
                "However, I'm currently experiencing technical difficulties. "
                "The system is working to restore full functionality. "
                "Please try again in a few moments, or try rephrasing your question."
            )

            # Execute LLM call with error handling and circuit breaker
            async def llm_call():
                return await self.llm.ainvoke(consultation.formatted_prompt)

            response = await llm_error_handler.safe_llm_call(
                provider_id=request.provider_id or "default",
                llm_func=llm_call,
                fallback_response=fallback_response
            )

            # Extract content from response (handle both string and object responses)
            if isinstance(response, str):
                raw_response = response
            elif hasattr(response, 'content'):
                raw_response = response.content
            else:
                raw_response = str(response)

            # Ensure we have a non-empty response
            if not raw_response or not raw_response.strip():
                logger.warning(f"LLM returned empty response for branch {request.branch_id}, using fallback")
                raw_response = fallback_response

            # Process response
            process_request = ProcessResponseRequest(
                branch_id=request.branch_id,
                provider_id=request.provider_id,
                raw_response=raw_response,
                original_query=request.query
            )

            result = await self.process_response(process_request)

            logger.info(f"Oracle consultation completed for branch {request.branch_id}")
            return result

        except Exception as e:
            logger.error(f"Failed to consult oracle: {e}", exc_info=True)

            # Create fallback response even on complete failure
            fallback_process_request = ProcessResponseRequest(
                branch_id=request.branch_id,
                provider_id=request.provider_id,
                raw_response=(
                    f"I apologize, but I'm currently unable to process your query: '{request.query}'. "
                    "The oracle service is experiencing technical difficulties. "
                    "Please try again later or contact support if the issue persists."
                ),
                original_query=request.query
            )

            try:
                # Try to process fallback response
                result = await self.process_response(fallback_process_request)
                logger.warning(f"Returned fallback response for branch {request.branch_id} due to error: {e}")
                return result
            except Exception as fallback_error:
                # If even fallback fails, raise the original error
                logger.error(f"Fallback response processing also failed: {fallback_error}")
                raise wrap_error(
                    e, DryadErrorCode.ORACLE_CONSULTATION_FAILED,
                    "Failed to consult oracle",
                    {"branch_id": request.branch_id, "provider_id": request.provider_id}
                )
    
    async def process_response(self, request: ProcessResponseRequest) -> ProcessResponseResult:
        """
        Process a response from an oracle.
        
        Args:
            request: Process response request
            
        Returns:
            Process response result
        """
        try:
            logger.debug(f"Processing oracle response for branch {request.branch_id}")
            
            # Validate branch exists
            branch_stmt = select(Branch).where(Branch.id == request.branch_id)
            branch_result = await self.db.execute(branch_stmt)
            branch = branch_result.scalar_one_or_none()
            
            if not branch:
                raise NotFoundError("Branch", request.branch_id)
            
            # Create dialogue
            dialogue_id = str(uuid.uuid4())
            dialogue = Dialogue(
                id=dialogue_id,
                branch_id=request.branch_id,
                oracle_used=request.provider_id,
                storage_path=f"dialogues/{request.branch_id}/{dialogue_id}.json"
            )
            
            # Create messages
            if request.original_query:
                human_message = DialogueMessage(
                    id=str(uuid.uuid4()),
                    dialogue_id=dialogue_id,
                    role=MessageRole.HUMAN,
                    content=request.original_query
                )
                dialogue.messages.append(human_message)
            
            oracle_message = DialogueMessage(
                id=str(uuid.uuid4()),
                dialogue_id=dialogue_id,
                role=MessageRole.ORACLE,
                content=request.raw_response
            )
            dialogue.messages.append(oracle_message)
            
            # Parse wisdom from response
            parsed_wisdom = await self._parse_wisdom(request.raw_response)
            dialogue.insights = {
                "themes": parsed_wisdom.themes,
                "facts": parsed_wisdom.facts,
                "decisions": parsed_wisdom.decisions,
                "questions": parsed_wisdom.questions
            }
            
            # Save dialogue
            self.db.add(dialogue)
            await self.db.flush()  # Flush to get the dialogue ID assigned
            await self.db.commit()

            # Count messages without accessing the relationship
            message_count = len(dialogue.messages) if dialogue.messages else 0

            result = ProcessResponseResult(
                dialogue_id=dialogue.id,
                parsed_wisdom=parsed_wisdom,
                message_count=message_count
            )
            
            logger.info(f"Oracle response processed successfully for branch {request.branch_id}")
            return result
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to process oracle response: {e}")
            raise wrap_error(
                e, DryadErrorCode.ORACLE_CONSULTATION_FAILED,
                "Failed to process oracle response",
                {"branch_id": request.branch_id, "provider_id": request.provider_id}
            )
    
    async def get_dialogues(self, branch_id: str) -> List[DialogueResponse]:
        """
        Get all dialogues for a branch.
        
        Args:
            branch_id: Branch ID
            
        Returns:
            List of dialogue responses
        """
        try:
            logger.debug(f"Getting dialogues for branch: {branch_id}")
            
            stmt = select(Dialogue).options(
                selectinload(Dialogue.messages)
            ).where(Dialogue.branch_id == branch_id).order_by(Dialogue.created_at.desc())
            
            result = await self.db.execute(stmt)
            dialogues = result.scalars().all()
            
            logger.debug(f"Retrieved {len(dialogues)} dialogues for branch {branch_id}")
            return [DialogueResponse.model_validate(dialogue) for dialogue in dialogues]
            
        except Exception as e:
            logger.error(f"Failed to get dialogues for branch {branch_id}: {e}")
            raise wrap_error(
                e, DryadErrorCode.DATABASE_ERROR,
                f"Failed to get dialogues for branch: {branch_id}",
                {"branch_id": branch_id}
            )
    
    async def get_dialogue(self, dialogue_id: str) -> Optional[DialogueResponse]:
        """
        Get a specific dialogue by ID.
        
        Args:
            dialogue_id: Dialogue ID
            
        Returns:
            Dialogue response or None if not found
        """
        try:
            logger.debug(f"Getting dialogue: {dialogue_id}")
            
            stmt = select(Dialogue).options(
                selectinload(Dialogue.messages),
                selectinload(Dialogue.branch)
            ).where(Dialogue.id == dialogue_id)
            
            result = await self.db.execute(stmt)
            dialogue = result.scalar_one_or_none()
            
            if not dialogue:
                logger.warning(f"Dialogue not found: {dialogue_id}")
                return None
            
            logger.debug(f"Dialogue retrieved: {dialogue_id}")
            return DialogueResponse.model_validate(dialogue)
            
        except Exception as e:
            logger.error(f"Failed to get dialogue {dialogue_id}: {e}")
            raise wrap_error(
                e, DryadErrorCode.DATABASE_ERROR,
                f"Failed to get dialogue: {dialogue_id}",
                {"dialogue_id": dialogue_id}
            )
    
    async def delete_dialogue(self, dialogue_id: str) -> None:
        """
        Delete a dialogue.
        
        Args:
            dialogue_id: Dialogue ID
        """
        try:
            logger.debug(f"Deleting dialogue: {dialogue_id}")
            
            stmt = select(Dialogue).where(Dialogue.id == dialogue_id)
            result = await self.db.execute(stmt)
            dialogue = result.scalar_one_or_none()
            
            if not dialogue:
                raise NotFoundError("Dialogue", dialogue_id)
            
            await self.db.delete(dialogue)
            await self.db.commit()
            
            logger.info(f"Dialogue deleted successfully: {dialogue_id}")
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to delete dialogue {dialogue_id}: {e}")
            raise wrap_error(
                e, DryadErrorCode.DATABASE_ERROR,
                f"Failed to delete dialogue: {dialogue_id}",
                {"dialogue_id": dialogue_id}
            )
    
    async def _build_consultation_prompt(
        self,
        vessel: Vessel,
        query: str,
        provider_id: str
    ) -> str:
        """Build context-aware prompt for LLM consultation."""
        # TODO: Load vessel content and build comprehensive prompt
        # For now, return a basic prompt
        
        prompt = f"""You are an AI oracle helping with knowledge exploration in a branching tree structure.

Current Query: {query}

Please provide a thoughtful response that builds on the existing context and helps advance the exploration. Consider multiple perspectives and suggest potential branching points for further exploration."""
        
        return prompt
    
    async def _parse_wisdom(self, response: str) -> ParsedWisdom:
        """Parse wisdom from oracle response."""
        # TODO: Implement intelligent parsing of themes, facts, decisions, questions
        # For now, return basic parsing
        
        return ParsedWisdom(
            themes=[],
            facts=[],
            decisions=[],
            questions=[],
            insights=[response[:200] + "..." if len(response) > 200 else response]
        )
