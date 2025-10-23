# DRYAD.AI React Chat App

A complete React chat application demonstrating the DRYAD.AI JavaScript SDK with modern React patterns, TypeScript, and styled-components.

## 🚀 Features

- **Real-time Chat Interface** with beautiful UI
- **Conversation Management** with persistent history
- **Markdown Rendering** with syntax highlighting
- **TypeScript Support** throughout
- **Styled Components** for modern styling
- **Error Handling** with user-friendly messages
- **Loading States** with progress indicators
- **Responsive Design** for all screen sizes

## 📦 Installation

```bash
# Install dependencies
npm install

# Start development server
npm start

# Build for production
npm run build
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory:

```bash
# DRYAD.AI API Configuration
REACT_APP_GREMLINS_AI_URL=http://localhost:8000
REACT_APP_GREMLINS_AI_API_KEY=your-api-key-here
```

### DRYAD.AI Server

Make sure your DRYAD.AI Backend is running:

```bash
# In your DRYAD.AI Backend directory
python start.py
```

The app will connect to `http://localhost:8000` by default.

## 🏗️ Project Structure

```
src/
├── App.tsx              # Main application component
├── index.tsx            # React app entry point
├── components/          # Reusable components
│   ├── ChatMessage.tsx  # Individual message component
│   ├── MessageInput.tsx # Message input component
│   └── LoadingSpinner.tsx # Loading indicator
├── hooks/               # Custom React hooks
│   ├── useDRYAD.AI.ts # DRYAD.AI client hook
│   └── useChat.ts       # Chat management hook
├── types/               # TypeScript type definitions
│   └── chat.ts          # Chat-related types
└── styles/              # Styled components
    └── theme.ts         # Theme configuration
```

## 🎨 Styling

This app uses **styled-components** for styling with a modern design system:

- **Gradient backgrounds** for visual appeal
- **Smooth animations** and transitions
- **Responsive design** for mobile and desktop
- **Dark/light theme** support (configurable)
- **Consistent spacing** and typography

## 🔌 DRYAD.AI Integration

### Client Setup

```typescript
import { DRYAD.AIClient } from '@gremlins-ai/sdk';

const client = new DRYAD.AIClient({
  baseUrl: process.env.REACT_APP_GREMLINS_AI_URL || 'http://localhost:8000',
  apiKey: process.env.REACT_APP_GREMLINS_AI_API_KEY,
});
```

### Key Features Used

- **Agent Invocation** - Send messages to AI
- **Conversation Management** - Create and manage conversations
- **Error Handling** - Graceful error handling
- **Health Checking** - Verify server connectivity

## 🧪 Testing

```bash
# Run tests
npm test

# Run tests with coverage
npm run test:coverage

# Run tests in watch mode
npm run test:watch
```

## 🚀 Deployment

### Build for Production

```bash
npm run build
```

### Deploy to Netlify

1. Build the project: `npm run build`
2. Deploy the `build` folder to Netlify
3. Set environment variables in Netlify dashboard

### Deploy to Vercel

1. Connect your GitHub repository to Vercel
2. Set environment variables in Vercel dashboard
3. Deploy automatically on push

### Docker Deployment

```dockerfile
FROM node:18-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## 🔧 Customization

### Adding New Features

1. **File Upload**: Add document upload functionality
2. **Voice Input**: Integrate speech-to-text
3. **Multi-Agent**: Support multi-agent workflows
4. **RAG Integration**: Add document Q&A features

### Styling Customization

Edit `src/styles/theme.ts` to customize:

- Colors and gradients
- Typography and fonts
- Spacing and layout
- Animation timings

### Component Customization

All components are modular and can be easily customized:

- `ChatMessage` - Individual message styling
- `MessageInput` - Input field and send button
- `LoadingSpinner` - Loading indicators

## 🐛 Troubleshooting

### Common Issues

1. **CORS Errors**
   - Ensure DRYAD.AI Backend allows your domain
   - Check CORS configuration in backend

2. **Connection Failed**
   - Verify DRYAD.AI server is running
   - Check the API URL in environment variables

3. **Build Errors**
   - Clear node_modules: `rm -rf node_modules && npm install`
   - Check TypeScript errors: `npm run type-check`

### Debug Mode

Enable debug logging:

```typescript
// In App.tsx
const client = new DRYAD.AIClient({
  baseUrl: process.env.REACT_APP_GREMLINS_AI_URL,
  apiKey: process.env.REACT_APP_GREMLINS_AI_API_KEY,
  // Add debug logging
  debug: process.env.NODE_ENV === 'development'
});
```

## 📚 Learn More

- [React Documentation](https://reactjs.org/)
- [TypeScript Documentation](https://www.typescriptlang.org/)
- [Styled Components Documentation](https://styled-components.com/)
- [DRYAD.AI Documentation](https://docs.DRYAD.AI.com)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This example is licensed under the MIT License - see the [LICENSE](../../../LICENSE) file for details.

---

**Happy coding with DRYAD.AI! 🤖✨**
