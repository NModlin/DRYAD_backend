from typing import List, Annotated, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from dryad.infrastructure.database import get_db
from dryad.domain.agent.models import Agent
from dryad.services.agent_factory import AgentFactory
from dryad.services.agent.runner import AgentRunner
from dryad.api.v1.auth import get_current_user

router = APIRouter()

class CreateAgentRequest(BaseModel):
    name: str
    system_prompt: str
    description: str = None
    model_name: str = "gpt-4o"

class AgentResponse(BaseModel):
    id: str
    name: str
    description: str = None
    model_name: str

class ChatRequest(BaseModel):
    message: str
    history: List[Dict[str, str]] = []

class ChatResponse(BaseModel):
    response: str

@router.post("/", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    agent_in: CreateAgentRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    factory = AgentFactory(db)
    agent = await factory.create_agent(
        name=agent_in.name,
        system_prompt=agent_in.system_prompt,
        user=current_user, # Passing User object model
        model_name=agent_in.model_name,
        description=agent_in.description
    )
    return AgentResponse(
        id=agent.id,
        name=agent.name,
        description=agent.description,
        model_name=agent.model_name
    )

@router.get("/", response_model=List[AgentResponse])
async def list_agents(
    db: Annotated[AsyncSession, Depends(get_db)]
):
    factory = AgentFactory(db)
    agents = await factory.list_agents()
    return [
        AgentResponse(
            id=a.id, 
            name=a.name, 
            description=a.description,
            model_name=a.model_name
        ) for a in agents
    ]

@router.post("/{agent_id}/chat", response_model=ChatResponse)
async def chat_with_agent(
    agent_id: str,
    chat_req: ChatRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    try:
        runner = AgentRunner(db, agent_id)
        # Note: In a real async system, we might offload this to a background task 
        # or use SSE/WebSockets for streaming. For request/response refactor, this blocks.
        response_text = await runner.chat(chat_req.message, chat_req.history)
        return ChatResponse(response=response_text)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        # Log error in prod
        raise HTTPException(status_code=500, detail=str(e))
