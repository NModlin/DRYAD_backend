import React, { useState, useEffect, useRef } from 'react';
import styled from 'styled-components';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';

import { GremlinsAIClient, Conversation, Message } from '@gremlins-ai/sdk';

// Styled Components
const AppContainer = styled.div`
  display: flex;
  flex-direction: column;
  height: 100vh;
  max-width: 1200px;
  margin: 0 auto;
  background: #f5f5f5;
`;

const Header = styled.header`
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 1rem 2rem;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
`;

const Title = styled.h1`
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
`;

const Subtitle = styled.p`
  margin: 0.5rem 0 0 0;
  opacity: 0.9;
  font-size: 0.9rem;
`;

const ChatContainer = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
`;

const MessagesContainer = styled.div`
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  background: white;
`;

const MessageBubble = styled.div<{ isUser: boolean }>`
  max-width: 70%;
  margin: 0.5rem 0;
  padding: 1rem 1.5rem;
  border-radius: 18px;
  background: ${props => props.isUser ? '#667eea' : '#f1f3f4'};
  color: ${props => props.isUser ? 'white' : '#333'};
  align-self: ${props => props.isUser ? 'flex-end' : 'flex-start'};
  margin-left: ${props => props.isUser ? 'auto' : '0'};
  margin-right: ${props => props.isUser ? '0' : 'auto'};
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
`;

const InputContainer = styled.div`
  display: flex;
  padding: 1rem;
  background: white;
  border-top: 1px solid #e0e0e0;
  gap: 1rem;
`;

const MessageInput = styled.textarea`
  flex: 1;
  padding: 1rem;
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  resize: none;
  font-family: inherit;
  font-size: 1rem;
  outline: none;
  transition: border-color 0.2s;

  &:focus {
    border-color: #667eea;
  }

  &::placeholder {
    color: #999;
  }
`;

const SendButton = styled.button`
  padding: 1rem 2rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  font-weight: 600;
  transition: transform 0.2s, box-shadow 0.2s;

  &:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
`;

const LoadingIndicator = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #666;
  font-style: italic;
  margin: 1rem 0;
`;

const ErrorMessage = styled.div`
  background: #fee;
  color: #c33;
  padding: 1rem;
  border-radius: 8px;
  margin: 1rem 0;
  border: 1px solid #fcc;
`;

const ConnectionStatus = styled.div<{ connected: boolean }>`
  padding: 0.5rem 1rem;
  background: ${props => props.connected ? '#d4edda' : '#f8d7da'};
  color: ${props => props.connected ? '#155724' : '#721c24'};
  text-align: center;
  font-size: 0.9rem;
`;

// Main App Component
const App: React.FC = () => {
  const [client, setClient] = useState<GremlinsAIClient | null>(null);
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Initialize client
  useEffect(() => {
    const initClient = async () => {
      try {
        const gremlinsClient = new GremlinsAIClient({
          baseUrl: process.env.REACT_APP_GREMLINS_AI_URL || 'http://localhost:8000',
          apiKey: process.env.REACT_APP_GREMLINS_AI_API_KEY,
        });

        // Test connection
        await gremlinsClient.getSystemHealth();
        setClient(gremlinsClient);
        setIsConnected(true);

        // Create initial conversation
        const newConversation = await gremlinsClient.createConversation('React Chat Session');
        setConversation(newConversation);
        
      } catch (err) {
        setError(`Failed to connect to GremlinsAI: ${err instanceof Error ? err.message : 'Unknown error'}`);
        setIsConnected(false);
      }
    };

    initClient();
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async () => {
    if (!client || !conversation || !inputValue.trim() || isLoading) return;

    const userMessage = inputValue.trim();
    setInputValue('');
    setError(null);
    setIsLoading(true);

    // Add user message to UI immediately
    const newUserMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: userMessage,
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, newUserMessage]);

    try {
      // Send to GremlinsAI
      const response = await client.invokeAgent({
        input: userMessage,
        conversation_id: conversation.id,
        save_conversation: true,
      });

      // Add AI response to UI
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.output,
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, aiMessage]);

    } catch (err) {
      setError(`Failed to send message: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const renderMessage = (message: Message) => (
    <MessageBubble key={message.id} isUser={message.role === 'user'}>
      {message.role === 'assistant' ? (
        <ReactMarkdown
          components={{
            code({ node, inline, className, children, ...props }) {
              const match = /language-(\w+)/.exec(className || '');
              return !inline && match ? (
                <SyntaxHighlighter
                  style={tomorrow}
                  language={match[1]}
                  PreTag="div"
                  {...props}
                >
                  {String(children).replace(/\n$/, '')}
                </SyntaxHighlighter>
              ) : (
                <code className={className} {...props}>
                  {children}
                </code>
              );
            },
          }}
        >
          {message.content}
        </ReactMarkdown>
      ) : (
        message.content
      )}
    </MessageBubble>
  );

  return (
    <AppContainer>
      <Header>
        <Title>🤖 GremlinsAI Chat</Title>
        <Subtitle>Powered by GremlinsAI React SDK</Subtitle>
      </Header>

      <ConnectionStatus connected={isConnected}>
        {isConnected ? '🟢 Connected to GremlinsAI' : '🔴 Disconnected from GremlinsAI'}
      </ConnectionStatus>

      <ChatContainer>
        <MessagesContainer>
          {messages.length === 0 && (
            <MessageBubble isUser={false}>
              👋 Hello! I'm your GremlinsAI assistant. How can I help you today?
            </MessageBubble>
          )}
          
          {messages.map(renderMessage)}
          
          {isLoading && (
            <LoadingIndicator>
              <span>🤔</span>
              <span>AI is thinking...</span>
            </LoadingIndicator>
          )}
          
          {error && <ErrorMessage>{error}</ErrorMessage>}
          
          <div ref={messagesEndRef} />
        </MessagesContainer>

        <InputContainer>
          <MessageInput
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message here... (Press Enter to send, Shift+Enter for new line)"
            rows={3}
            disabled={!isConnected || isLoading}
          />
          <SendButton
            onClick={sendMessage}
            disabled={!isConnected || !inputValue.trim() || isLoading}
          >
            {isLoading ? '⏳' : '📤'} Send
          </SendButton>
        </InputContainer>
      </ChatContainer>
    </AppContainer>
  );
};

export default App;
