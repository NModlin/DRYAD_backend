#!/usr/bin/env python3
"""
Multi-Agent Workflow Example - DRYAD.AI Python SDK

This example demonstrates multi-agent workflows with the DRYAD.AI platform.
Shows how to:
- Execute different workflow types
- Work with specialized agents
- Handle complex multi-step processes
- Monitor workflow execution
"""

import asyncio
import logging
from typing import Dict, Any

from dryad_ai import DRYAD.AIClient
from dryad_ai.exceptions import DRYAD.AIError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def agent_capabilities_example():
    """Explore available agents and their capabilities."""
    
    print("🤖 Agent Capabilities Example")
    print("=" * 40)
    
    try:
        async with DRYAD.AIClient() as client:
            
            # Get agent capabilities
            agents = await client.get_agent_capabilities()
            
            print(f"Available Agents: {len(agents)}")
            print()
            
            for name, agent in agents.items():
                print(f"🤖 {name.title()} Agent")
                print(f"   Role: {agent.role}")
                print(f"   Available: {'✅' if agent.available else '❌'}")
                if hasattr(agent, 'capabilities') and agent.capabilities:
                    print(f"   Capabilities: {agent.capabilities}")
                if hasattr(agent, 'tools') and agent.tools:
                    print(f"   Tools: {agent.tools}")
                print()
                
    except DRYAD.AIError as e:
        logger.error(f"Error getting agent capabilities: {e}")


async def simple_research_workflow():
    """Execute a simple research workflow."""
    
    print("🔍 Simple Research Workflow")
    print("=" * 40)
    
    try:
        async with DRYAD.AIClient() as client:
            
            research_topics = [
                "Latest developments in quantum computing",
                "Impact of AI on healthcare industry",
                "Renewable energy trends in 2024"
            ]
            
            for i, topic in enumerate(research_topics, 1):
                print(f"\n--- Research Task {i} ---")
                print(f"Topic: {topic}")
                print("🔄 Executing workflow...")
                
                result = await client.execute_multi_agent_workflow(
                    workflow_type="simple_research",
                    input_text=topic
                )
                
                print(f"✅ Workflow completed!")
                print(f"Agents used: {', '.join(result['agents_used'])}")
                print(f"Execution time: {result['execution_time']:.2f}s")
                print(f"Result preview: {result['result'][:200]}...")
                print()
                
    except DRYAD.AIError as e:
        logger.error(f"Error in research workflow: {e}")


async def complex_analysis_workflow():
    """Execute a complex multi-step analysis workflow."""
    
    print("📊 Complex Analysis Workflow")
    print("=" * 40)
    
    try:
        async with DRYAD.AIClient() as client:
            
            # Create a conversation to track the workflow
            conversation = await client.create_conversation(
                title="Complex Analysis - AI in Education"
            )
            
            analysis_request = """
            Conduct a comprehensive analysis of artificial intelligence applications in education.
            
            Please cover:
            1. Current AI tools being used in classrooms
            2. Benefits and challenges of AI in education
            3. Future trends and predictions
            4. Recommendations for educators and institutions
            
            Provide a detailed, well-structured analysis with examples and data where possible.
            """
            
            print("🔄 Starting complex analysis workflow...")
            print("This may take a while as multiple agents collaborate...")
            
            result = await client.execute_multi_agent_workflow(
                workflow_type="research_analyze_write",
                input_text=analysis_request,
                conversation_id=conversation.id,
                save_conversation=True
            )
            
            print(f"✅ Complex workflow completed!")
            print(f"Agents involved: {', '.join(result['agents_used'])}")
            print(f"Total execution time: {result['execution_time']:.2f}s")
            print(f"Conversation ID: {conversation.id}")
            
            # Display the structured result
            print("\n📋 Analysis Result:")
            print("=" * 50)
            print(result['result'])
            
            # Show the conversation history
            print("\n💬 Conversation History:")
            print("=" * 30)
            
            full_conversation = await client.get_conversation(conversation.id)
            for msg in full_conversation.messages:
                role_emoji = "👤" if msg.role == "user" else "🤖"
                print(f"{role_emoji} {msg.role.title()}: {msg.content[:100]}...")
                print()
                
    except DRYAD.AIError as e:
        logger.error(f"Error in complex analysis workflow: {e}")


async def collaborative_writing_workflow():
    """Execute a collaborative writing workflow."""
    
    print("✍️  Collaborative Writing Workflow")
    print("=" * 40)
    
    try:
        async with DRYAD.AIClient() as client:
            
            writing_prompts = [
                {
                    "topic": "The Future of Remote Work",
                    "type": "blog_post",
                    "requirements": "Write a 500-word blog post about remote work trends, including statistics and expert opinions."
                },
                {
                    "topic": "Sustainable Technology Solutions",
                    "type": "article",
                    "requirements": "Create an informative article about green technology innovations, focusing on practical applications."
                }
            ]
            
            for i, prompt in enumerate(writing_prompts, 1):
                print(f"\n--- Writing Task {i} ---")
                print(f"Topic: {prompt['topic']}")
                print(f"Type: {prompt['type']}")
                print("🔄 Collaborative writing in progress...")
                
                # Create a conversation for this writing task
                conversation = await client.create_conversation(
                    title=f"Writing: {prompt['topic']}"
                )
                
                result = await client.execute_multi_agent_workflow(
                    workflow_type="collaborative_writing",
                    input_text=f"Topic: {prompt['topic']}\n\nRequirements: {prompt['requirements']}",
                    conversation_id=conversation.id,
                    save_conversation=True
                )
                
                print(f"✅ Writing completed!")
                print(f"Collaborating agents: {', '.join(result['agents_used'])}")
                print(f"Writing time: {result['execution_time']:.2f}s")
                print(f"Word count: ~{len(result['result'].split())} words")
                
                # Show a preview of the written content
                print(f"\n📝 Content Preview:")
                print("-" * 30)
                preview = result['result'][:300] + "..." if len(result['result']) > 300 else result['result']
                print(preview)
                print()
                
    except DRYAD.AIError as e:
        logger.error(f"Error in collaborative writing workflow: {e}")


async def workflow_with_conversation_context():
    """Demonstrate workflow execution with conversation context."""
    
    print("💬 Workflow with Conversation Context")
    print("=" * 40)
    
    try:
        async with DRYAD.AIClient() as client:
            
            # Create a conversation and build context
            conversation = await client.create_conversation(
                title="Technology Discussion with Context"
            )
            
            # Build conversation context
            context_messages = [
                "I'm interested in learning about blockchain technology.",
                "Specifically, I want to understand its applications beyond cryptocurrency.",
                "I work in supply chain management, so practical applications would be helpful."
            ]
            
            print("🔄 Building conversation context...")
            for msg in context_messages:
                await client.invoke_agent(
                    msg,
                    conversation_id=conversation.id,
                    save_conversation=True
                )
                print(f"Added context: {msg}")
            
            # Now execute a workflow with this context
            print("\n🔄 Executing workflow with established context...")
            
            workflow_request = """
            Based on our previous discussion about my interest in blockchain for supply chain management,
            please provide a comprehensive analysis of:
            
            1. Specific blockchain applications in supply chain
            2. Case studies of successful implementations
            3. Challenges and solutions
            4. Implementation roadmap for a mid-size company
            """
            
            result = await client.execute_multi_agent_workflow(
                workflow_type="research_analyze_write",
                input_text=workflow_request,
                conversation_id=conversation.id,
                save_conversation=True
            )
            
            print(f"✅ Context-aware workflow completed!")
            print(f"Agents used: {', '.join(result['agents_used'])}")
            print(f"Execution time: {result['execution_time']:.2f}s")
            
            # Show how the context influenced the result
            print(f"\n📋 Contextual Analysis Result:")
            print("=" * 40)
            print(result['result'][:500] + "...")
            
            # Show the full conversation
            print(f"\n💬 Full Conversation ({conversation.id[:8]}...):")
            print("=" * 40)
            
            full_conversation = await client.get_conversation(conversation.id)
            print(f"Total messages: {len(full_conversation.messages)}")
            
            # Show last few messages
            for msg in full_conversation.messages[-3:]:
                role_emoji = "👤" if msg.role == "user" else "🤖"
                print(f"{role_emoji} {msg.role.title()}: {msg.content[:150]}...")
                print()
                
    except DRYAD.AIError as e:
        logger.error(f"Error in context workflow: {e}")


async def workflow_comparison():
    """Compare different workflow types on the same input."""
    
    print("⚖️  Workflow Type Comparison")
    print("=" * 40)
    
    try:
        async with DRYAD.AIClient() as client:
            
            test_input = "Analyze the environmental impact of electric vehicles compared to traditional gasoline cars."
            
            workflow_types = [
                "simple_research",
                "research_analyze_write",
                "complex_analysis"
            ]
            
            results = {}
            
            for workflow_type in workflow_types:
                print(f"\n🔄 Testing workflow: {workflow_type}")
                
                try:
                    result = await client.execute_multi_agent_workflow(
                        workflow_type=workflow_type,
                        input_text=test_input
                    )
                    
                    results[workflow_type] = {
                        'agents_used': result['agents_used'],
                        'execution_time': result['execution_time'],
                        'result_length': len(result['result']),
                        'result_preview': result['result'][:200] + "..."
                    }
                    
                    print(f"✅ Completed in {result['execution_time']:.2f}s")
                    print(f"Agents: {', '.join(result['agents_used'])}")
                    print(f"Output length: {len(result['result'])} characters")
                    
                except DRYAD.AIError as e:
                    print(f"❌ Failed: {e}")
                    results[workflow_type] = {'error': str(e)}
            
            # Summary comparison
            print(f"\n📊 Workflow Comparison Summary")
            print("=" * 50)
            
            for workflow_type, data in results.items():
                print(f"\n🔧 {workflow_type.replace('_', ' ').title()}")
                if 'error' in data:
                    print(f"   Status: ❌ Failed - {data['error']}")
                else:
                    print(f"   Agents: {', '.join(data['agents_used'])}")
                    print(f"   Time: {data['execution_time']:.2f}s")
                    print(f"   Output: {data['result_length']} chars")
                    print(f"   Preview: {data['result_preview']}")
                    
    except Exception as e:
        logger.error(f"Error in workflow comparison: {e}")


async def main():
    """Run all multi-agent workflow examples."""
    
    print("🚀 DRYAD.AI Multi-Agent Workflow Examples")
    print("=" * 60)
    
    examples = [
        ("Agent Capabilities", agent_capabilities_example),
        ("Simple Research", simple_research_workflow),
        ("Complex Analysis", complex_analysis_workflow),
        ("Collaborative Writing", collaborative_writing_workflow),
        ("Context-Aware Workflow", workflow_with_conversation_context),
        ("Workflow Comparison", workflow_comparison)
    ]
    
    for name, example_func in examples:
        print(f"\n{'='*60}")
        print(f"Running: {name}")
        print(f"{'='*60}")
        
        try:
            await example_func()
        except Exception as e:
            logger.error(f"Example '{name}' failed: {e}")
        
        # Pause between examples
        print(f"\n✅ {name} completed. Press Enter to continue...")
        input()
    
    print(f"\n🎉 All multi-agent workflow examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
