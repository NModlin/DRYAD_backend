#!/usr/bin/env python3
"""
Basic Chat Example - DRYAD.AI Python SDK

This example demonstrates basic chat functionality with the DRYAD.AI platform.
Shows how to:
- Initialize the client
- Send messages to the AI agent
- Handle responses and errors
- Manage conversations
"""

import asyncio
import logging
from typing import Optional

from dryad_ai import DRYAD.AIClient
from dryad_ai.exceptions import DRYAD.AIError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def basic_chat_example():
    """Basic chat example with error handling."""
    
    print("🤖 DRYAD.AI Basic Chat Example")
    print("=" * 40)
    
    try:
        # Initialize the client
        async with DRYAD.AIClient(base_url="http://localhost:8000") as client:
            
            # Simple chat without conversation persistence
            print("\n1. Simple Chat (no conversation)")
            response = await client.invoke_agent("What is artificial intelligence?")
            
            print(f"AI Response: {response['output']}")
            print(f"Execution Time: {response['execution_time']:.2f}s")
            
            # Chat with conversation persistence
            print("\n2. Chat with Conversation Persistence")
            
            # Create a new conversation
            conversation = await client.create_conversation(title="AI Discussion")
            print(f"Created conversation: {conversation.id}")
            
            # Send messages in the conversation
            messages = [
                "Hello! Can you explain machine learning?",
                "What are the main types of machine learning?",
                "Can you give me an example of supervised learning?"
            ]
            
            for i, message in enumerate(messages, 1):
                print(f"\n--- Message {i} ---")
                print(f"User: {message}")
                
                response = await client.invoke_agent(
                    message,
                    conversation_id=conversation.id,
                    save_conversation=True
                )
                
                print(f"AI: {response['output'][:200]}...")
                print(f"Execution Time: {response['execution_time']:.2f}s")
            
            # Retrieve the full conversation
            print("\n3. Retrieving Full Conversation")
            full_conversation = await client.get_conversation(conversation.id)
            
            print(f"Conversation: {full_conversation.title}")
            print(f"Total Messages: {len(full_conversation.messages)}")
            
            for msg in full_conversation.messages[-4:]:  # Show last 4 messages
                print(f"  {msg.role}: {msg.content[:100]}...")
            
    except DRYAD.AIError as e:
        logger.error(f"DRYAD.AI Error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")


async def interactive_chat():
    """Interactive chat session."""
    
    print("\n🤖 Interactive Chat Mode")
    print("Type 'quit' to exit")
    print("=" * 40)
    
    conversation_id: Optional[str] = None
    
    try:
        async with DRYAD.AIClient() as client:
            
            # Create a conversation for the session
            conversation = await client.create_conversation(title="Interactive Chat")
            conversation_id = conversation.id
            print(f"Started conversation: {conversation_id}")
            
            while True:
                try:
                    # Get user input
                    user_input = input("\nYou: ").strip()
                    
                    if user_input.lower() in ['quit', 'exit', 'bye']:
                        print("👋 Goodbye!")
                        break
                    
                    if not user_input:
                        continue
                    
                    # Send to AI
                    print("🤔 Thinking...")
                    response = await client.invoke_agent(
                        user_input,
                        conversation_id=conversation_id,
                        save_conversation=True
                    )
                    
                    print(f"AI: {response['output']}")
                    
                except KeyboardInterrupt:
                    print("\n👋 Goodbye!")
                    break
                except DRYAD.AIError as e:
                    print(f"❌ Error: {e}")
                except Exception as e:
                    print(f"❌ Unexpected error: {e}")
                    
    except Exception as e:
        logger.error(f"Failed to start interactive chat: {e}")


async def conversation_management_example():
    """Example of conversation management operations."""
    
    print("\n📝 Conversation Management Example")
    print("=" * 40)
    
    try:
        async with DRYAD.AIClient() as client:
            
            # List existing conversations
            print("1. Listing existing conversations...")
            conversations = await client.list_conversations(limit=5)
            
            if conversations:
                print(f"Found {len(conversations)} conversations:")
                for conv in conversations:
                    print(f"  - {conv.id[:8]}... | {conv.title or 'Untitled'} | {conv.created_at}")
            else:
                print("No existing conversations found.")
            
            # Create multiple conversations
            print("\n2. Creating new conversations...")
            topics = [
                "Science Discussion",
                "Technology Trends",
                "Creative Writing"
            ]
            
            created_conversations = []
            for topic in topics:
                conv = await client.create_conversation(title=topic)
                created_conversations.append(conv)
                print(f"Created: {conv.title} ({conv.id[:8]}...)")
                
                # Add a sample message to each
                await client.invoke_agent(
                    f"Let's discuss {topic.lower()}. What should we start with?",
                    conversation_id=conv.id,
                    save_conversation=True
                )
            
            # Demonstrate conversation retrieval
            print("\n3. Retrieving conversation details...")
            for conv in created_conversations[:2]:  # Show first 2
                full_conv = await client.get_conversation(conv.id)
                print(f"\nConversation: {full_conv.title}")
                print(f"Messages: {len(full_conv.messages)}")
                
                for msg in full_conv.messages:
                    print(f"  {msg.role}: {msg.content[:80]}...")
            
    except DRYAD.AIError as e:
        logger.error(f"DRYAD.AI Error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")


async def error_handling_example():
    """Example of proper error handling."""
    
    print("\n⚠️  Error Handling Example")
    print("=" * 40)
    
    # Example with invalid base URL
    try:
        async with DRYAD.AIClient(base_url="http://invalid-url:9999") as client:
            await client.invoke_agent("This will fail")
    except DRYAD.AIError as e:
        print(f"✅ Caught expected error: {e}")
    
    # Example with timeout
    try:
        async with DRYAD.AIClient(timeout=0.001) as client:  # Very short timeout
            await client.invoke_agent("This might timeout")
    except DRYAD.AIError as e:
        print(f"✅ Caught timeout error: {e}")
    
    # Example with invalid conversation ID
    try:
        async with DRYAD.AIClient() as client:
            await client.get_conversation("invalid-conversation-id")
    except DRYAD.AIError as e:
        print(f"✅ Caught invalid ID error: {e}")


async def main():
    """Run all examples."""
    
    print("🚀 DRYAD.AI Python SDK Examples")
    print("=" * 50)
    
    # Run examples
    await basic_chat_example()
    await conversation_management_example()
    await error_handling_example()
    
    # Ask if user wants interactive mode
    print("\n" + "=" * 50)
    choice = input("Would you like to try interactive chat? (y/n): ").strip().lower()
    
    if choice in ['y', 'yes']:
        await interactive_chat()
    
    print("\n✅ Examples completed!")


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())
