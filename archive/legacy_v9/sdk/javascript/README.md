# DRYAD.AI JavaScript/TypeScript SDK

[![npm version](https://badge.fury.io/js/%40gremlins-ai%2Fsdk.svg)](https://badge.fury.io/js/%40gremlins-ai%2Fsdk)
[![TypeScript](https://img.shields.io/badge/TypeScript-Ready-blue.svg)](https://www.typescriptlang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Documentation](https://img.shields.io/badge/docs-latest-brightgreen.svg)](https://docs.DRYAD.AI.com)

The official JavaScript/TypeScript SDK for the DRYAD.AI platform - a comprehensive AI backend with multi-agent workflows, vector search, multimodal processing, and real-time capabilities.

## 🚀 Features

- **Modern ES6+ Syntax** - Built with modern JavaScript and full TypeScript support
- **Node.js & Browser Compatible** - Works in both server and client environments
- **Type Safety** - Complete TypeScript definitions with IntelliSense support
- **Multi-Agent Workflows** - Orchestrate complex AI agent interactions
- **Vector Search & RAG** - Semantic search and retrieval-augmented generation
- **Multimodal Processing** - Handle text, audio, video, and images
- **Real-time Communication** - WebSocket support with EventEmitter pattern
- **Automatic Error Handling** - Robust error handling with custom exceptions
- **Automatic Retries** - Built-in retry logic with exponential backoff
- **Tree-shakeable** - Optimized for modern bundlers

## 📦 Installation

```bash
# Install from npm
npm install @gremlins-ai/sdk

# Install with Yarn
yarn add @gremlins-ai/sdk

# Install with pnpm
pnpm add @gremlins-ai/sdk
```

## 🏃 Quick Start

### Basic Chat

```typescript
import { DRYAD.AIClient } from '@gremlins-ai/sdk';

const client = new DRYAD.AIClient({
  baseUrl: 'http://localhost:8000',
  apiKey: 'your-api-key' // Optional for development
});

// Simple AI interaction
const response = await client.invokeAgent('What is artificial intelligence?');
console.log(response.output);
```

### Conversation Management

```typescript
import { DRYAD.AIClient } from '@gremlins-ai/sdk';

const client = new DRYAD.AIClient();

// Create a conversation
const conversation = await client.createConversation('AI Discussion');

// Send messages in context
const response1 = await client.invokeAgent({
  input: 'Explain machine learning',
  conversation_id: conversation.id,
  save_conversation: true
});

const response2 = await client.invokeAgent({
  input: 'What are the main types?', // Contextual follow-up
  conversation_id: conversation.id,
  save_conversation: true
});

// Retrieve full conversation
const fullConversation = await client.getConversation(conversation.id);
console.log(`Total messages: ${fullConversation.messages.length}`);
```

### Document Processing & RAG

```typescript
import { DRYAD.AIClient } from '@gremlins-ai/sdk';

const client = new DRYAD.AIClient();

// Upload and process document
const fileInput = document.getElementById('file-input') as HTMLInputElement;
const file = fileInput.files[0];

const document = await client.uploadDocument({
  file,
  filename: file.name,
  processForRAG: true
});

// Query with RAG
const response = await client.queryWithRAG({
  query: 'What are the key findings in the document?',
  document_ids: [document.id]
});

console.log(`Answer: ${response.answer}`);
console.log(`Sources: ${response.sources?.length || 0}`);
```

### Multi-Agent Workflows

```typescript
import { DRYAD.AIClient } from '@gremlins-ai/sdk';

const client = new DRYAD.AIClient();

// Execute multi-agent workflow
const result = await client.executeMultiAgentWorkflow({
  task: 'Research and write a report on renewable energy',
  agents: ['researcher', 'analyst', 'writer'],
  workflow_type: 'sequential'
});

console.log(`Final result: ${result.final_output}`);
console.log(`Agent interactions: ${result.agent_interactions.length}`);
```

### Real-time WebSocket Communication

```typescript
import { DRYAD.AIClient } from '@gremlins-ai/sdk';

const client = new DRYAD.AIClient();

// Connect to real-time endpoint
const websocket = client.connectRealtime('/ws');

websocket.on('connected', () => {
  console.log('Connected to DRYAD.AI');
});

websocket.on('message', (message) => {
  console.log('Received:', message);
});

websocket.on('error', (error) => {
  console.error('WebSocket error:', error);
});

// Send message
websocket.send({
  type: 'chat',
  content: 'Hello, AI!'
});
```

## 🔧 Configuration

### Environment Variables

```bash
# Optional: Set default base URL
export GREMLINS_AI_BASE_URL=http://localhost:8000

# Optional: Set API key for authentication
export GREMLINS_AI_API_KEY=your-api-key
```

### Client Configuration

```typescript
import { DRYAD.AIClient } from '@gremlins-ai/sdk';

const client = new DRYAD.AIClient({
  baseUrl: 'http://localhost:8000',
  apiKey: 'your-api-key',        // Optional
  timeout: 30000,                // Request timeout in milliseconds
  maxRetries: 3,                 // Maximum retry attempts
  retryDelay: 1000,              // Initial retry delay
  maxRetryDelay: 60000,          // Maximum retry delay
  userAgent: 'my-app/1.0.0',     // Custom user agent
});
```

### TypeScript Configuration

Add to your `tsconfig.json`:

```json
{
  "compilerOptions": {
    "moduleResolution": "node",
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true
  }
}
```

## 🌐 Browser Usage

### ES Modules

```html
<script type="module">
  import { DRYAD.AIClient } from 'https://unpkg.com/@gremlins-ai/sdk@latest/dist/index.esm.js';
  
  const client = new DRYAD.AIClient({
    baseUrl: 'http://localhost:8000'
  });
  
  const response = await client.invokeAgent('Hello from the browser!');
  console.log(response.output);
</script>
```

### UMD (Universal Module Definition)

```html
<script src="https://unpkg.com/@gremlins-ai/sdk@latest/dist/index.js"></script>
<script>
  const client = new DRYAD.AI.DRYAD.AIClient({
    baseUrl: 'http://localhost:8000'
  });
  
  client.invokeAgent('Hello from UMD!').then(response => {
    console.log(response.output);
  });
</script>
```

## 🧪 Testing

```bash
# Run tests
npm test

# Run tests with coverage
npm run test:coverage

# Run tests in watch mode
npm run test:watch

# Type checking
npm run type-check
```

## 🏗️ Building

```bash
# Build for production
npm run build

# Build and watch for changes
npm run build:watch

# Clean build directory
npm run clean
```

## 📚 API Reference

### Client Methods

- `invokeAgent(request)` - Send message to AI agent
- `createConversation(request)` - Create new conversation
- `listConversations(request)` - List conversations
- `getConversation(id)` - Get conversation details
- `deleteConversation(id)` - Delete conversation
- `uploadDocument(request)` - Upload document
- `queryWithRAG(request)` - Query with RAG
- `executeMultiAgentWorkflow(request)` - Execute workflow
- `getSystemHealth()` - Get system health
- `connectRealtime(endpoint)` - Connect WebSocket

### Error Handling

```typescript
import { 
  DRYAD.AIError, 
  APIError, 
  ValidationError, 
  AuthenticationError,
  RateLimitError,
  ConnectionError,
  TimeoutError 
} from '@gremlins-ai/sdk';

try {
  const response = await client.invokeAgent('Hello!');
} catch (error) {
  if (error instanceof AuthenticationError) {
    console.error('Authentication failed:', error.message);
  } else if (error instanceof RateLimitError) {
    console.error(`Rate limited. Retry after: ${error.retryAfter}s`);
  } else if (error instanceof ValidationError) {
    console.error('Validation errors:', error.validationErrors);
  } else if (error instanceof DRYAD.AIError) {
    console.error('DRYAD.AI error:', error.getUserMessage());
  } else {
    console.error('Unexpected error:', error);
  }
}
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](../../CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](../../LICENSE) file for details.

## 🆘 Support

- **Documentation**: https://docs.DRYAD.AI.com
- **Issues**: https://github.com/your-org/DRYAD_backend/issues
- **Discussions**: https://github.com/your-org/DRYAD_backend/discussions
- **Email**: support@DRYAD.AI.com

## 🎯 Roadmap

- [ ] React hooks package (`@gremlins-ai/react`)
- [ ] Vue.js composables package (`@gremlins-ai/vue`)
- [ ] Angular services package (`@gremlins-ai/angular`)
- [ ] Streaming responses for long operations
- [ ] Advanced caching mechanisms
- [ ] Plugin system for custom extensions

---

**Built with ❤️ by the DRYAD.AI Team**
