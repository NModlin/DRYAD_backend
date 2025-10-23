# DRYAD.AI Python SDK

[![PyPI version](https://badge.fury.io/py/gremlins-ai.svg)](https://badge.fury.io/py/gremlins-ai)
[![Python Support](https://img.shields.io/pypi/pyversions/gremlins-ai.svg)](https://pypi.org/project/gremlins-ai/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Documentation](https://img.shields.io/badge/docs-latest-brightgreen.svg)](https://docs.DRYAD.AI.com)

The official Python SDK for the DRYAD.AI platform - a comprehensive AI backend with multi-agent workflows, vector search, multimodal processing, and real-time capabilities.

## 🚀 Features

- **Async/Await Support** - Built for modern Python with full async support
- **Type Safety** - Complete type hints and Pydantic models
- **Multi-Agent Workflows** - Orchestrate complex AI agent interactions
- **Vector Search & RAG** - Semantic search and retrieval-augmented generation
- **Multimodal Processing** - Handle text, audio, video, and images
- **Real-time Communication** - WebSocket support for live interactions
- **GraphQL Integration** - Advanced querying capabilities
- **Comprehensive Error Handling** - Robust error handling with custom exceptions
- **Automatic Retries** - Built-in retry logic with exponential backoff
- **Connection Pooling** - Efficient HTTP connection management

## 📦 Installation

```bash
# Install from PyPI
pip install gremlins-ai

# Install with development dependencies
pip install gremlins-ai[dev]

# Install with documentation dependencies
pip install gremlins-ai[docs]

# Install from source
git clone https://github.com/your-org/DRYAD_backend.git
cd DRYAD_backend/sdk/python
pip install -e .
```

## 🏃 Quick Start

### Basic Chat

```python
import asyncio
from gremlins_ai import DRYAD.AIClient

async def main():
    async with DRYAD.AIClient(base_url="http://localhost:8000") as client:
        # Simple AI interaction
        response = await client.invoke_agent("What is artificial intelligence?")
        print(response['output'])

asyncio.run(main())
```

### Conversation Management

```python
import asyncio
from gremlins_ai import DRYAD.AIClient

async def conversation_example():
    async with DRYAD.AIClient() as client:
        # Create a conversation
        conversation = await client.create_conversation(title="AI Discussion")
        
        # Send messages in context
        response1 = await client.invoke_agent(
            "Explain machine learning",
            conversation_id=conversation.id,
            save_conversation=True
        )
        
        response2 = await client.invoke_agent(
            "What are the main types?",  # Contextual follow-up
            conversation_id=conversation.id,
            save_conversation=True
        )
        
        # Retrieve full conversation
        full_conversation = await client.get_conversation(conversation.id)
        print(f"Total messages: {len(full_conversation.messages)}")

asyncio.run(conversation_example())
```

### Multi-Agent Workflows

```python
import asyncio
from gremlins_ai import DRYAD.AIClient

async def multi_agent_example():
    async with DRYAD.AIClient() as client:
        # Execute multi-agent workflow
        result = await client.execute_multi_agent_workflow(
            task="Research and write a report on renewable energy",
            agents=["researcher", "analyst", "writer"],
            workflow_type="sequential"
        )
        
        print(f"Final result: {result['final_output']}")
        print(f"Agent interactions: {len(result['agent_interactions'])}")

asyncio.run(multi_agent_example())
```

### Document Processing & RAG

```python
import asyncio
from gremlins_ai import DRYAD.AIClient

async def document_rag_example():
    async with DRYAD.AIClient() as client:
        # Upload and process document
        with open("document.pdf", "rb") as f:
            document = await client.upload_document(
                file=f,
                filename="document.pdf",
                process_for_rag=True
            )
        
        # Query with RAG
        response = await client.query_with_rag(
            query="What are the key findings in the document?",
            document_ids=[document.id]
        )
        
        print(f"Answer: {response['answer']}")
        print(f"Sources: {response['sources']}")

asyncio.run(document_rag_example())
```

### Real-time WebSocket Communication

```python
import asyncio
from gremlins_ai import DRYAD.AIClient

async def websocket_example():
    async with DRYAD.AIClient() as client:
        # Connect to real-time endpoint
        async with client.connect_realtime() as websocket:
            # Send message
            await websocket.send_message({
                "type": "chat",
                "content": "Hello, AI!"
            })
            
            # Listen for responses
            async for message in websocket:
                print(f"Received: {message}")
                if message.get("type") == "response":
                    break

asyncio.run(websocket_example())
```

## 📚 Documentation

- **[API Reference](https://docs.DRYAD.AI.com/sdk/python/api)** - Complete API documentation
- **[Examples](https://docs.DRYAD.AI.com/sdk/python/examples)** - Comprehensive examples
- **[Tutorials](https://docs.DRYAD.AI.com/sdk/python/tutorials)** - Step-by-step guides
- **[Migration Guide](https://docs.DRYAD.AI.com/sdk/python/migration)** - Upgrading between versions

## 🔧 Configuration

### Environment Variables

```bash
# Optional: Set default base URL
export GREMLINS_AI_BASE_URL=http://localhost:8000

# Optional: Set API key for authentication
export GREMLINS_AI_API_KEY=your-api-key

# Optional: Set default timeout
export GREMLINS_AI_TIMEOUT=30
```

### Client Configuration

```python
from gremlins_ai import DRYAD.AIClient

client = DRYAD.AIClient(
    base_url="http://localhost:8000",
    api_key="your-api-key",  # Optional
    timeout=30,              # Request timeout in seconds
    max_retries=3,           # Maximum retry attempts
    retry_delay=1.0,         # Initial retry delay
    max_retry_delay=60.0,    # Maximum retry delay
)
```

## 🧪 Testing

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=gremlins_ai

# Run specific test file
pytest tests/test_client.py

# Run async tests
pytest -v tests/test_async_client.py
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: https://docs.DRYAD.AI.com
- **Issues**: https://github.com/your-org/DRYAD_backend/issues
- **Discussions**: https://github.com/your-org/DRYAD_backend/discussions
- **Email**: support@DRYAD.AI.com

## 🎯 Roadmap

- [ ] GraphQL subscription support
- [ ] Streaming responses for long-running operations
- [ ] Advanced caching mechanisms
- [ ] Plugin system for custom extensions
- [ ] Integration with popular ML frameworks

---

**Built with ❤️ by the DRYAD.AI Team**
