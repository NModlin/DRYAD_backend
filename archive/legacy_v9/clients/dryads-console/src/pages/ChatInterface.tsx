import React, { useState, useEffect, useRef } from 'react'
import { useQuery, useMutation } from 'react-query'
import {
  Send,
  Paperclip,
  Code,
  Brain,
  TreePine,
  BookOpen,
  Folder,
  Users,
  Zap,
  Search,
  History,
  Settings,
  MessageSquare,
  Bot,
  User,
  Plus,
  Trash2
} from 'lucide-react'
import {
  ChatMessage,
  ChatSession,
  CommandSuggestion,
  Grove,
  Branch,
  Agent
} from '../types'
import { dryadAPI } from '../services/api'

const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputText, setInputText] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [activeSession, setActiveSession] = useState<ChatSession | null>(null)
  const [commandSuggestions, setCommandSuggestions] = useState<CommandSuggestion[]>([])
  const [showContextPanel, setShowContextPanel] = useState(true)
  const [selectedGrove, setSelectedGrove] = useState<Grove | null>(null)
  const [selectedBranch, setSelectedBranch] = useState<Branch | null>(null)
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null)
  const [chatSessions, setChatSessions] = useState<ChatSession[]>([])
  const [showSessionPanel, setShowSessionPanel] = useState(false)
  
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Fetch user's groves
  const { data: groves } = useQuery('user-groves', () => dryadAPI.listGroves())
  // Fetch available agents
  const { data: agents } = useQuery('available-agents', () => dryadAPI.listAgents())

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Initialize with welcome message and load sessions
  useEffect(() => {
    if (messages.length === 0) {
      const welcomeMessage: ChatMessage = {
        id: '1',
        type: 'system',
        content: 'Welcome to The Dryads Console! I\'m your unified interface to DRYAD.AI. You can ask me about your groves, consult the oracle, manage files, or explore your knowledge tree. What would you like to do?',
        timestamp: new Date().toISOString(),
        sender: 'System',
        context: { showQuickActions: true }
      }
      setMessages([welcomeMessage])
      
      // Create initial session
      const initialSession: ChatSession = {
        id: 'default',
        title: 'Main Conversation',
        messages: [welcomeMessage],
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      }
      setChatSessions([initialSession])
      setActiveSession(initialSession)
    }
  }, [messages.length])

  // Load saved sessions from API
  useEffect(() => {
    const loadSessions = async () => {
      try {
        const sessions = await dryadAPI.getChatSessions()
        setChatSessions(sessions.items || [])
      } catch (error) {
        console.log('No saved sessions found')
      }
    }
    loadSessions()
  }, [])

  // Generate command suggestions based on input
  useEffect(() => {
    if (inputText.trim().length > 0) {
      const suggestions = generateCommandSuggestions(inputText)
      setCommandSuggestions(suggestions)
    } else {
      setCommandSuggestions([])
    }
  }, [inputText])

  const generateCommandSuggestions = (text: string): CommandSuggestion[] => {
    const baseSuggestions: CommandSuggestion[] = [
      {
        id: 'grove-explore',
        command: 'Explore my groves',
        description: 'Navigate through your knowledge trees',
        icon: TreePine,
        action: () => handleCommand('show groves')
      },
      {
        id: 'oracle-consult',
        command: 'Consult the oracle',
        description: 'Get AI insights on any topic',
        icon: Brain,
        action: () => handleCommand('consult oracle')
      },
      {
        id: 'memory-search',
        command: 'Search memories',
        description: 'Find past conversations and insights',
        icon: BookOpen,
        action: () => handleCommand('search memories')
      },
      {
        id: 'file-manage',
        command: 'Manage files',
        description: 'Access your documents and storage',
        icon: Folder,
        action: () => handleCommand('show files')
      },
      {
        id: 'agent-interact',
        command: 'Talk to agents',
        description: 'Interact with university agents',
        icon: Users,
        action: () => handleCommand('list agents')
      }
    ]

    return baseSuggestions.filter(suggestion => 
      suggestion.command.toLowerCase().includes(text.toLowerCase()) ||
      suggestion.description.toLowerCase().includes(text.toLowerCase())
    )
  }

  const handleCommand = async (command: string) => {
    setIsLoading(true)
    
    // Add user message
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: command,
      timestamp: new Date().toISOString(),
      sender: 'You'
    }
    
    const updatedMessages = [...messages, userMessage]
    setMessages(updatedMessages)
    setInputText('')

    // Update active session
    if (activeSession) {
      const updatedSession: ChatSession = {
        ...activeSession,
        messages: updatedMessages,
        updatedAt: new Date().toISOString()
      }
      setActiveSession(updatedSession)
      setChatSessions(prev => prev.map(s => s.id === updatedSession.id ? updatedSession : s))
    }

    // Process command and generate response
    try {
      const response = await processCommand(command)
      const systemMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'system',
        content: response.content,
        timestamp: new Date().toISOString(),
        sender: 'Dryads Console',
        context: response.context
      }
      
      const finalMessages = [...updatedMessages, systemMessage]
      setMessages(finalMessages)

      // Update session with final messages
      if (activeSession) {
        const finalSession: ChatSession = {
          ...activeSession,
          messages: finalMessages,
          updatedAt: new Date().toISOString()
        }
        setActiveSession(finalSession)
        setChatSessions(prev => prev.map(s => s.id === finalSession.id ? finalSession : s))
      }
    } catch (error) {
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'error',
        content: 'I encountered an error processing your request. Please try again.',
        timestamp: new Date().toISOString(),
        sender: 'System'
      }
      
      const errorMessages = [...updatedMessages, errorMessage]
      setMessages(errorMessages)
    } finally {
      setIsLoading(false)
    }
  }

  const createNewSession = () => {
    const newSession: ChatSession = {
      id: Date.now().toString(),
      title: `Conversation ${chatSessions.length + 1}`,
      messages: [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    }
    
    setChatSessions(prev => [newSession, ...prev])
    setActiveSession(newSession)
    setMessages([])
    setShowSessionPanel(false)
  }

  const switchSession = (session: ChatSession) => {
    setActiveSession(session)
    setMessages(session.messages)
    setShowSessionPanel(false)
  }

  const deleteSession = (sessionId: string) => {
    if (chatSessions.length <= 1) return
    
    setChatSessions(prev => prev.filter(s => s.id !== sessionId))
    
    if (activeSession?.id === sessionId) {
      const remainingSessions = chatSessions.filter(s => s.id !== sessionId)
      if (remainingSessions.length > 0) {
        switchSession(remainingSessions[0])
      } else {
        createNewSession()
      }
    }
  }

  const processCommand = async (command: string): Promise<{ content: string; context?: any }> => {
    const lowerCommand = command.toLowerCase()

    // Grove-related commands
    if (lowerCommand.includes('grove') || lowerCommand.includes('tree') || lowerCommand.includes('explore')) {
      const grovesData = await dryadAPI.listGroves()
      return {
        content: `I found ${grovesData.items?.length || 0} groves in your knowledge tree. Here's an overview of your groves:`,
        context: { 
          type: 'grove-list',
          groves: grovesData.items,
          showActions: true 
        }
      }
    }

    // Oracle consultation
    if (lowerCommand.includes('consult') || lowerCommand.includes('oracle') || lowerCommand.includes('ai')) {
      return {
        content: 'I can help you consult the oracle. Please specify what you\'d like to ask about, or I can show you available AI providers.',
        context: { 
          type: 'oracle-prompt',
          showProviderSelection: true 
        }
      }
    }

    // Memory search
    if (lowerCommand.includes('memory') || lowerCommand.includes('search') || lowerCommand.includes('find')) {
      return {
        content: 'I can help you search through your memories. What would you like to find? You can search by content, tags, or context.',
        context: { 
          type: 'memory-search',
          showSearchInterface: true 
        }
      }
    }

    // File management
    if (lowerCommand.includes('file') || lowerCommand.includes('document') || lowerCommand.includes('storage')) {
      return {
        content: 'I can help you manage your files. You can upload, search, or organize files across local storage and Google Drive.',
        context: { 
          type: 'file-management',
          showFileActions: true 
        }
      }
    }

    // Agent interaction
    if (lowerCommand.includes('agent') || lowerCommand.includes('university') || lowerCommand.includes('talk')) {
      const agentsData = agents || { items: [] }
      return {
        content: `I found ${agentsData.items.length} agents available. You can interact with memory keepers, professors, or specialized agents.`,
        context: { 
          type: 'agent-list',
          agents: agentsData.items,
          showSelection: true 
        }
      }
    }

    // Default response for unrecognized commands
    return {
      content: 'I understand you\'re asking about something. I can help you with:\n\n• Exploring your knowledge groves and branches\n• Consulting AI providers for insights\n• Searching through your memory records\n• Managing files and documents\n• Interacting with university agents\n\nWhat specific action would you like to take?',
      context: { showQuickActions: true }
    }
  }

  const handleSendMessage = () => {
    if (inputText.trim() && !isLoading) {
      handleCommand(inputText.trim())
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const renderMessageContent = (message: ChatMessage) => {
    if (message.context?.type === 'grove-list') {
      return (
        <div className="space-y-4">
          <p>{message.content}</p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {message.context.groves?.slice(0, 4).map((grove: Grove) => (
              <div key={grove.id} className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                <div className="flex items-center space-x-3">
                  <TreePine className="w-5 h-5 text-green-600" />
                  <div>
                    <h4 className="font-medium text-gray-900">{grove.name}</h4>
                    <p className="text-sm text-gray-600">
                      {grove.branchCount} branches • {grove.dialogueCount} dialogues
                    </p>
                  </div>
                </div>
                <button 
                  onClick={() => handleCommand(`explore grove ${grove.name}`)}
                  className="mt-2 text-sm text-primary-600 hover:text-primary-700"
                >
                  Explore this grove →
                </button>
              </div>
            ))}
          </div>
        </div>
      )
    }

    if (message.context?.type === 'oracle-prompt') {
      return (
        <div className="space-y-4">
          <p>{message.content}</p>
          <div className="flex space-x-3">
            <button 
              onClick={() => handleCommand('show oracle providers')}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
            >
              Show Providers
            </button>
            <button 
              onClick={() => setInputText('I want to ask the oracle about: ')}
              className="px-4 py-2 border border-purple-600 text-purple-600 rounded-lg hover:bg-purple-50 transition-colors"
            >
              Ask a Question
            </button>
          </div>
        </div>
      )
    }

    // Default text message
    return <p className="whitespace-pre-wrap">{message.content}</p>
  }

  const QuickActions = () => (
    <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-6">
      <button 
        onClick={() => handleCommand('explore my groves')}
        className="flex items-center space-x-2 p-3 bg-blue-50 border border-blue-200 rounded-lg hover:bg-blue-100 transition-colors"
      >
        <TreePine className="w-5 h-5 text-blue-600" />
        <span className="text-sm font-medium text-blue-900">Explore Groves</span>
      </button>
      <button 
        onClick={() => handleCommand('consult oracle')}
        className="flex items-center space-x-2 p-3 bg-purple-50 border border-purple-200 rounded-lg hover:bg-purple-100 transition-colors"
      >
        <Brain className="w-5 h-5 text-purple-600" />
        <span className="text-sm font-medium text-purple-900">Consult Oracle</span>
      </button>
      <button 
        onClick={() => handleCommand('search memories')}
        className="flex items-center space-x-2 p-3 bg-green-50 border border-green-200 rounded-lg hover:bg-green-100 transition-colors"
      >
        <BookOpen className="w-5 h-5 text-green-600" />
        <span className="text-sm font-medium text-green-900">Search Memories</span>
      </button>
      <button 
        onClick={() => handleCommand('manage files')}
        className="flex items-center space-x-2 p-3 bg-orange-50 border border-orange-200 rounded-lg hover:bg-orange-100 transition-colors"
      >
        <Folder className="w-5 h-5 text-orange-600" />
        <span className="text-sm font-medium text-orange-900">Manage Files</span>
      </button>
      <button 
        onClick={() => handleCommand('talk to agents')}
        className="flex items-center space-x-2 p-3 bg-indigo-50 border border-indigo-200 rounded-lg hover:bg-indigo-100 transition-colors"
      >
        <Users className="w-5 h-5 text-indigo-600" />
        <span className="text-sm font-medium text-indigo-900">Agent Chat</span>
      </button>
      <button 
        onClick={() => handleCommand('system status')}
        className="flex items-center space-x-2 p-3 bg-gray-50 border border-gray-200 rounded-lg hover:bg-gray-100 transition-colors"
      >
        <Zap className="w-5 h-5 text-gray-600" />
        <span className="text-sm font-medium text-gray-900">System Info</span>
      </button>
    </div>
  )

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <MessageSquare className="w-6 h-6 text-purple-600" />
            <div>
              <h1 className="text-xl font-bold text-gray-900">Dryads Console</h1>
              <p className="text-sm text-gray-600">Unified chat interface for DRYAD.AI</p>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <button
              onClick={() => setShowContextPanel(!showContextPanel)}
              className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              title="Toggle Context Panel"
            >
              <Search className="w-5 h-5" />
            </button>
            <button
              onClick={() => setShowSessionPanel(!showSessionPanel)}
              className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              title="Manage Conversations"
            >
              <History className="w-5 h-5" />
            </button>
            <button className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              title="Settings">
              <Settings className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Main Chat Area */}
        <div className="flex-1 flex flex-col">
          {/* Messages Area */}
          <div className="flex-1 overflow-auto p-6">
            <div className="max-w-4xl mx-auto space-y-6">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex space-x-3 ${
                    message.type === 'user' ? 'flex-row-reverse space-x-reverse' : ''
                  }`}
                >
                  <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                    message.type === 'user' ? 'bg-primary-100' :
                    message.type === 'system' ? 'bg-purple-100' :
                    message.type === 'error' ? 'bg-red-100' : 'bg-gray-100'
                  }`}>
                    {message.type === 'user' ? (
                      <User className="w-4 h-4 text-primary-600" />
                    ) : (
                      <Bot className="w-4 h-4 text-purple-600" />
                    )}
                  </div>
                  <div className={`flex-1 min-w-0 ${
                    message.type === 'user' ? 'text-right' : ''
                  }`}>
                    <div className={`inline-block max-w-lg rounded-lg p-4 ${
                      message.type === 'user' ? 'bg-primary-600 text-white' :
                      message.type === 'system' ? 'bg-white border border-gray-200 shadow-soft' :
                      message.type === 'error' ? 'bg-red-50 border border-red-200 text-red-800' :
                      'bg-gray-50 border border-gray-200'
                    }`}>
                      <div className="text-sm font-medium mb-1">
                        {message.sender}
                      </div>
                      {renderMessageContent(message)}
                    </div>
                    <div className={`text-xs text-gray-500 mt-1 ${
                      message.type === 'user' ? 'text-right' : ''
                    }`}>
                      {new Date(message.timestamp).toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              ))}
              
              {isLoading && (
                <div className="flex space-x-3">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center quantum-pulse">
                    <Bot className="w-4 h-4 text-purple-600" />
                  </div>
                  <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-soft chat-message-quantum">
                    <div className="flex items-center space-x-2 text-gray-600">
                      <div>Thinking</div>
                      <div className="thinking-dots">
                        <div className="thinking-dot"></div>
                        <div className="thinking-dot"></div>
                        <div className="thinking-dot"></div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>
          </div>

          {/* Quick Actions */}
          {messages.length === 1 && <QuickActions />}

          {/* Input Area */}
          <div className="border-t border-gray-200 bg-white p-6">
            <div className="max-w-4xl mx-auto">
              {/* Command Suggestions */}
              {commandSuggestions.length > 0 && (
                <div className="mb-4 space-y-2">
                  {commandSuggestions.slice(0, 3).map((suggestion) => (
                    <button
                      key={suggestion.id}
                      onClick={suggestion.action}
                      className="flex items-center space-x-3 w-full p-3 text-left bg-gray-50 hover:bg-gray-100 rounded-lg border border-gray-200 transition-colors quantum-command-suggestion"
                    >
                      <suggestion.icon className="w-4 h-4 text-gray-600 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-gray-900">{suggestion.command}</div>
                        <div className="text-sm text-gray-600">{suggestion.description}</div>
                      </div>
                    </button>
                  ))}
                </div>
              )}

              {/* Input Field */}
              <div className="flex space-x-4">
                <div className="flex-1 relative">
                  <textarea
                    ref={inputRef}
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Ask about your groves, consult the oracle, manage files, or talk to agents..."
                    className="w-full h-16 p-4 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none chat-input-quantum"
                    disabled={isLoading}
                  />
                  <div className="absolute right-3 bottom-3 flex items-center space-x-2">
                    <button className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
                      title="Attach File">
                      <Paperclip className="w-4 h-4" />
                    </button>
                    <button className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
                      title="Insert Code">
                      <Code className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                <button
                  onClick={handleSendMessage}
                  disabled={!inputText.trim() || isLoading}
                  className="px-6 py-4 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center space-x-2"
                >
                  <Send className="w-4 h-4" />
                  <span>Send</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Session Management Panel */}
        {showSessionPanel && (
          <div className="w-80 bg-white border-l border-gray-200 flex flex-col">
            <div className="p-4 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h3 className="font-medium text-gray-900">Conversations</h3>
                <button
                  onClick={createNewSession}
                  className="p-1 text-gray-600 hover:text-gray-900 transition-colors"
                  title="New Conversation"
                >
                  <Plus className="w-4 h-4" />
                </button>
              </div>
            </div>
            <div className="flex-1 overflow-auto p-4">
              <div className="space-y-2">
                {chatSessions.map((session) => (
                  <div
                    key={session.id}
                    className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                      activeSession?.id === session.id
                        ? 'bg-primary-50 border-primary-300'
                        : 'bg-gray-50 border-gray-200 hover:bg-gray-100'
                    }`}
                    onClick={() => switchSession(session)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1 min-w-0">
                        <h4 className="font-medium text-gray-900 truncate">{session.title}</h4>
                        <p className="text-xs text-gray-600">
                          {session.messages.length} messages • {new Date(session.updatedAt).toLocaleDateString()}
                        </p>
                      </div>
                      {chatSessions.length > 1 && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            deleteSession(session.id)
                          }}
                          className="p-1 text-gray-400 hover:text-red-600 transition-colors ml-2"
                          title="Delete Conversation"
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Context Panel */}
        {showContextPanel && !showSessionPanel && (
          <div className="w-80 bg-white border-l border-gray-200 flex flex-col">
            <div className="p-4 border-b border-gray-200">
              <h3 className="font-medium text-gray-900">Current Context</h3>
            </div>
            <div className="flex-1 overflow-auto p-4">
              <div className="space-y-4">
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Active Session</h4>
                  <div className="text-sm text-gray-600">
                    {activeSession?.title || 'Main Conversation'}
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Active Grove</h4>
                  <div className="text-sm text-gray-600">
                    {selectedGrove ? selectedGrove.name : 'No grove selected'}
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Active Agent</h4>
                  <div className="text-sm text-gray-600">
                    {selectedAgent ? selectedAgent.name : 'Console Assistant'}
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Quick Commands</h4>
                  <div className="space-y-1">
                    <button
                      onClick={() => handleCommand('system status')}
                      className="block w-full text-left text-sm text-gray-600 hover:text-gray-900 py-1"
                    >
                      Check system status
                    </button>
                    <button
                      onClick={() => handleCommand('help')}
                      className="block w-full text-left text-sm text-gray-600 hover:text-gray-900 py-1"
                    >
                      Show help guide
                    </button>
                    <button
                      onClick={() => setShowSessionPanel(true)}
                      className="block w-full text-left text-sm text-gray-600 hover:text-gray-900 py-1"
                    >
                      Manage conversations
                    </button>
                    <button
                      onClick={createNewSession}
                      className="block w-full text-left text-sm text-gray-600 hover:text-gray-900 py-1"
                    >
                      Start new conversation
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default ChatInterface