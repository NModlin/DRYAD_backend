# Dryad Console

A professional management interface for the DRYAD.AI backend. The Dryad Console provides a comprehensive interface for interacting with 20+ specialized agents through an intuitive chat experience.

## Features

- **Real-time Chat**: Seamless conversation with AI agents
- **Multi-Agent Support**: Choose from 20+ specialized agents
- **Conversation History**: Persistent chat sessions
- **Markdown Support**: Rich text rendering with code highlighting
- **Agent Selection**: Dropdown to choose specific agents
- **WebSocket Integration**: Real-time updates and progress tracking

## Quick Start

### Prerequisites

- Node.js (v16 or higher)
- npm or yarn
- Dryad.AI backend running on `http://localhost:8000`

### Installation

1. **Clone or navigate to this directory**:
   ```bash
   cd examples/frameworks/react-chat-app
   ```

2. **Run setup script** (choose based on your OS):

   **Windows:**
   ```cmd
   setup.bat
   ```

   **Linux/Mac:**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

3. **Configure environment** (if needed):
   Edit the `.env` file to point to your Dryad backend:
   ```env
   REACT_APP_DRYAD_AI_URL=http://localhost:8000
   REACT_APP_DRYAD_AI_API_KEY=your-api-key-here
   ```

4. **Start the development server**:
   ```bash
   npm start
   ```

5. **Open your browser** to `http://localhost:3000`

## API Endpoints Used

The interface connects to the following Dryad.AI endpoints:

- **Agent Chat**: `POST /api/v1/agent/chat` - Main chat endpoint with conversation context
- **Conversation Management**: `GET/POST /api/v1/chat-history/conversations` - Manage chat sessions
- **Agent Registry**: `GET /api/v1/agent-registry/agents` - List available agents
- **Health Check**: `GET /api/v1/health/` - Verify backend connectivity

## Available Agents

The interface automatically discovers and displays all available agents from the Dryad registry, including:

- **Orchestrator Agents**: Master coordination and workflow management
- **Specialist Agents**: Domain-specific expertise (coding, analysis, research)
- **Execution Agents**: Task execution and tool usage

## Customization

### Adding New Agent Types

To add support for additional agent types, modify the `AgentSelector` component in `src/App.tsx`:

```typescript
// Add new agent options
<option value="custom_agent">Custom Agent</option>
```

### Styling

The interface uses styled-components for styling. Modify the styled components in `src/App.tsx` to customize the appearance.

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `REACT_APP_DRYAD_AI_URL` | Dryad backend URL | `http://localhost:8000` |
| `REACT_APP_DRYAD_AI_API_KEY` | API key for authentication | (optional) |
| `REACT_APP_ENV` | Environment mode | `development` |

## Development

### Project Structure

```
src/
├── App.tsx                 # Main application component
├── dryad-client.ts         # Dryad.AI API client
├── index.tsx              # Application entry point
└── ...                    # Other React files
```

### Building for Production

```bash
npm run build
```

The build artifacts will be stored in the `build/` directory.

## Troubleshooting

### Common Issues

1. **Connection Failed**: Ensure the Dryad backend is running on the configured URL
2. **Agents Not Loading**: Check if the agent registry endpoint is accessible
3. **Build Errors**: Verify all dependencies are installed with `npm install`

### Debug Mode

Enable debug logging by setting the environment variable:
```env
REACT_APP_DEBUG=true
```

## Integration with Dryad Backend

This interface is designed to work seamlessly with the Dryad.AI backend architecture:

- **Agent Registry Integration**: Automatically discovers and displays available agents
- **Conversation Context**: Maintains conversation history for context-aware responses
- **Multi-Agent Orchestration**: Supports both single-agent and multi-agent workflows
- **Real-time Communication**: Uses WebSocket for live updates

## Contributing

To contribute to this interface:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with a running Dryad backend
5. Submit a pull request

## License

This project is part of the Dryad.AI ecosystem and follows the same licensing terms.

## Support

For issues and questions:
- Check the Dryad.AI documentation
- Open an issue in the repository
- Contact the Dryad.AI development team
