# app/core/agent.py
import logging
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from typing import TypedDict, Annotated, List, Union
import operator
logger = logging.getLogger(__name__)

# LLM configuration using local models
from app.core.llm_config import get_llm, get_llm_info

# Initialize LLM (supports local models like Ollama, Hugging Face, etc.)
try:
    llm = get_llm()
    llm_info = get_llm_info()
    logger.info(f"🤖 Agent initialized with {llm_info['provider']} LLM: {llm_info['model_name']}")
except Exception as e:
    logger.error(f"❌ Failed to initialize LLM for agent: {e}")
    raise RuntimeError(f"Agent system requires functional LLM. Cannot initialize without AI capabilities: {e}")

# 1. Define the state
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]
    agent_outcome: Union[AgentAction, AgentFinish, None]

# 3. Define the agent logic with genuine AI reasoning
def run_agent(data: AgentState) -> dict:
    """Execute genuine AI reasoning using local LLM."""
    messages = data.get('messages', [])
    if not messages:
        return {"agent_outcome": AgentFinish(return_values={"output": "No input provided"}, log="")}

    last_message = messages[-1]
    if isinstance(last_message, HumanMessage):
        query = last_message.content
        logger.info(f"🤖 AI Agent processing query with reasoning: {query}")

        try:
            # Use genuine AI reasoning instead of search fallback
            from app.core.llm_config import get_llm
            llm = get_llm()

            # Create a comprehensive prompt for AI reasoning
            ai_prompt = f"""You are an intelligent AI assistant. Analyze and respond to the following query with reasoning and insights:

Query: {query}

Please provide a thoughtful, comprehensive response that demonstrates:
1. Understanding of the query context and intent
2. Relevant knowledge and insights
3. Practical advice or information
4. Clear reasoning behind your response

If you need current information that you don't have, acknowledge this limitation and provide the best response possible based on your knowledge."""

            # Get AI response using local LLM
            ai_response = llm.invoke(ai_prompt)

            # Extract the response content
            if hasattr(ai_response, 'content'):
                response_content = ai_response.content
            else:
                response_content = str(ai_response)

            logger.info("✅ AI Agent generated intelligent response using local LLM")

            # Create a response message
            response_message = AIMessage(content=response_content)

            return {
                "messages": [response_message],
                "agent_outcome": AgentFinish(return_values={"output": response_content}, log="AI reasoning completed")
            }

        except Exception as e:
            logger.error(f"❌ AI Agent execution failed: {e}")
            # No fallback to search - if AI fails, it should fail explicitly
            error_message = f"AI Agent system error: {e}. The AI reasoning system needs to be properly configured."
            return {"agent_outcome": AgentFinish(return_values={"output": error_message}, log="AI system error")}

    return {"agent_outcome": AgentFinish(return_values={"output": "Unable to process request"}, log="")}

# 4. Define the conditional edge logic
def should_continue(data: AgentState) -> str:
    """Determines whether to continue the loop or end."""
    if isinstance(data.get('agent_outcome'), AgentFinish):
        return "end"
    else:
        return "continue"

# 5. Define the graph
workflow = StateGraph(AgentState)
workflow.add_node("agent", run_agent)
workflow.set_entry_point("agent")
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {"continue": "agent", "end": END}
)
agent_graph_app = workflow.compile()
