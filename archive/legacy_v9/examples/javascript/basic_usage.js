/**
 * Basic Usage Example - DRYAD.AI JavaScript SDK
 * 
 * This example demonstrates basic usage of the DRYAD.AI platform using JavaScript.
 * Shows how to:
 * - Make HTTP requests to the API
 * - Handle responses and errors
 * - Work with conversations
 * - Use different API endpoints
 */

// Using fetch API (available in modern browsers and Node.js 18+)
// For older Node.js versions, install node-fetch: npm install node-fetch

const BASE_URL = 'http://localhost:8000';

/**
 * Simple HTTP client for DRYAD.AI API
 */
class DRYAD.AIClient {
    constructor(baseUrl = BASE_URL, apiKey = null) {
        this.baseUrl = baseUrl.replace(/\/$/, '');
        this.apiKey = apiKey;
    }

    /**
     * Make an HTTP request to the API
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };

        if (this.apiKey) {
            headers['Authorization'] = `Bearer ${this.apiKey}`;
        }

        const config = {
            ...options,
            headers
        };

        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(`API Error ${response.status}: ${errorData.message || 'Unknown error'}`);
            }

            return await response.json();
        } catch (error) {
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                throw new Error('Network error: Unable to connect to DRYAD.AI API');
            }
            throw error;
        }
    }

    /**
     * Invoke the AI agent
     */
    async invokeAgent(input, conversationId = null, saveConversation = false) {
        const payload = {
            input,
            save_conversation: saveConversation
        };

        if (conversationId) {
            payload.conversation_id = conversationId;
        }

        return await this.request('/api/v1/agent/invoke', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
    }

    /**
     * Create a new conversation
     */
    async createConversation(title = null) {
        const payload = title ? { title } : {};
        return await this.request('/api/v1/history/conversations', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
    }

    /**
     * Get a conversation by ID
     */
    async getConversation(conversationId) {
        return await this.request(`/api/v1/history/conversations/${conversationId}`);
    }

    /**
     * List conversations
     */
    async listConversations(limit = 10, offset = 0) {
        const params = new URLSearchParams({ limit, offset });
        return await this.request(`/api/v1/history/conversations?${params}`);
    }

    /**
     * Execute multi-agent workflow
     */
    async executeMultiAgentWorkflow(workflowType, input, conversationId = null, saveConversation = false) {
        const payload = {
            workflow_type: workflowType,
            input,
            save_conversation: saveConversation
        };

        if (conversationId) {
            payload.conversation_id = conversationId;
        }

        return await this.request('/api/v1/multi-agent/execute', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
    }

    /**
     * Search documents
     */
    async searchDocuments(query, limit = 5, useRag = false) {
        const payload = {
            query,
            limit,
            use_rag: useRag
        };

        return await this.request('/api/v1/documents/search', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
    }

    /**
     * Get system health
     */
    async getSystemHealth() {
        return await this.request('/api/v1/realtime/system/status');
    }
}

/**
 * Basic chat example
 */
async function basicChatExample() {
    console.log('🤖 Basic Chat Example');
    console.log('='.repeat(40));

    const client = new DRYAD.AIClient();

    try {
        // Simple chat
        console.log('\n1. Simple Chat');
        const response = await client.invokeAgent('What is machine learning?');
        
        console.log(`AI Response: ${response.output}`);
        console.log(`Execution Time: ${response.execution_time.toFixed(2)}s`);

        // Chat with conversation
        console.log('\n2. Chat with Conversation');
        const conversation = await client.createConversation('ML Discussion');
        console.log(`Created conversation: ${conversation.id}`);

        const messages = [
            'Can you explain neural networks?',
            'What are the different types of neural networks?',
            'How do convolutional neural networks work?'
        ];

        for (let i = 0; i < messages.length; i++) {
            console.log(`\n--- Message ${i + 1} ---`);
            console.log(`User: ${messages[i]}`);

            const response = await client.invokeAgent(
                messages[i],
                conversation.id,
                true
            );

            console.log(`AI: ${response.output.substring(0, 200)}...`);
            console.log(`Execution Time: ${response.execution_time.toFixed(2)}s`);
        }

        // Retrieve full conversation
        console.log('\n3. Full Conversation');
        const fullConversation = await client.getConversation(conversation.id);
        console.log(`Conversation: ${fullConversation.title}`);
        console.log(`Total Messages: ${fullConversation.messages.length}`);

    } catch (error) {
        console.error('❌ Error:', error.message);
    }
}

/**
 * Multi-agent workflow example
 */
async function multiAgentExample() {
    console.log('\n🤖 Multi-Agent Workflow Example');
    console.log('='.repeat(40));

    const client = new DRYAD.AIClient();

    try {
        const topics = [
            'Latest developments in renewable energy',
            'Impact of AI on job market',
            'Future of space exploration'
        ];

        for (let i = 0; i < topics.length; i++) {
            console.log(`\n--- Research Task ${i + 1} ---`);
            console.log(`Topic: ${topics[i]}`);
            console.log('🔄 Executing workflow...');

            const result = await client.executeMultiAgentWorkflow(
                'simple_research',
                topics[i]
            );

            console.log('✅ Workflow completed!');
            console.log(`Agents used: ${result.agents_used.join(', ')}`);
            console.log(`Execution time: ${result.execution_time.toFixed(2)}s`);
            console.log(`Result preview: ${result.result.substring(0, 200)}...`);
        }

    } catch (error) {
        console.error('❌ Error:', error.message);
    }
}

/**
 * Document search example
 */
async function documentSearchExample() {
    console.log('\n📄 Document Search Example');
    console.log('='.repeat(40));

    const client = new DRYAD.AIClient();

    try {
        const queries = [
            'artificial intelligence applications',
            'machine learning algorithms',
            'data science best practices'
        ];

        for (const query of queries) {
            console.log(`\n🔍 Searching: "${query}"`);

            // Search without RAG
            const searchResults = await client.searchDocuments(query, 3, false);
            console.log(`Found ${searchResults.results.length} documents`);

            searchResults.results.forEach((result, index) => {
                console.log(`  ${index + 1}. ${result.title} (score: ${result.score.toFixed(3)})`);
                console.log(`     ${result.content.substring(0, 100)}...`);
            });

            // Search with RAG
            console.log('\n🧠 RAG-enhanced search...');
            const ragResults = await client.searchDocuments(query, 3, true);
            
            if (ragResults.rag_response) {
                console.log('RAG Response:');
                console.log(ragResults.rag_response.substring(0, 300) + '...');
            }
        }

    } catch (error) {
        console.error('❌ Error:', error.message);
    }
}

/**
 * System monitoring example
 */
async function systemMonitoringExample() {
    console.log('\n📊 System Monitoring Example');
    console.log('='.repeat(40));

    const client = new DRYAD.AIClient();

    try {
        const health = await client.getSystemHealth();
        
        console.log(`System Status: ${health.status.toUpperCase()}`);
        console.log(`Version: ${health.version}`);
        console.log(`Uptime: ${health.uptime.toFixed(1)}s`);
        console.log(`Active Tasks: ${health.active_tasks}`);
        
        console.log('\nComponents:');
        health.components.forEach(component => {
            const status = component.available ? '✅ Available' : '❌ Unavailable';
            console.log(`  ${component.name}: ${status}`);
        });

    } catch (error) {
        console.error('❌ Error:', error.message);
    }
}

/**
 * WebSocket example
 */
async function webSocketExample() {
    console.log('\n🔌 WebSocket Example');
    console.log('='.repeat(40));

    // Note: This requires WebSocket support
    if (typeof WebSocket === 'undefined') {
        console.log('❌ WebSocket not available in this environment');
        return;
    }

    try {
        const ws = new WebSocket('ws://localhost:8000/api/v1/ws/ws');

        ws.onopen = () => {
            console.log('✅ WebSocket connected');
            
            // Subscribe to system updates
            ws.send(JSON.stringify({
                type: 'subscribe',
                subscription_type: 'system'
            }));
        };

        ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            console.log('📨 Received:', message);
        };

        ws.onerror = (error) => {
            console.error('❌ WebSocket error:', error);
        };

        ws.onclose = () => {
            console.log('🔌 WebSocket disconnected');
        };

        // Keep connection alive for a few seconds
        setTimeout(() => {
            ws.close();
        }, 5000);

    } catch (error) {
        console.error('❌ WebSocket error:', error.message);
    }
}

/**
 * Error handling example
 */
async function errorHandlingExample() {
    console.log('\n⚠️  Error Handling Example');
    console.log('='.repeat(40));

    // Test with invalid URL
    const invalidClient = new DRYAD.AIClient('http://invalid-url:9999');

    try {
        await invalidClient.invokeAgent('This will fail');
    } catch (error) {
        console.log('✅ Caught expected error:', error.message);
    }

    // Test with invalid conversation ID
    const client = new DRYAD.AIClient();
    try {
        await client.getConversation('invalid-conversation-id');
    } catch (error) {
        console.log('✅ Caught invalid ID error:', error.message);
    }
}

/**
 * Main function to run all examples
 */
async function main() {
    console.log('🚀 DRYAD.AI JavaScript Examples');
    console.log('='.repeat(50));

    const examples = [
        { name: 'Basic Chat', func: basicChatExample },
        { name: 'Multi-Agent Workflow', func: multiAgentExample },
        { name: 'Document Search', func: documentSearchExample },
        { name: 'System Monitoring', func: systemMonitoringExample },
        { name: 'WebSocket Communication', func: webSocketExample },
        { name: 'Error Handling', func: errorHandlingExample }
    ];

    for (const example of examples) {
        try {
            await example.func();
        } catch (error) {
            console.error(`❌ Example '${example.name}' failed:`, error.message);
        }
        
        // Pause between examples (in Node.js)
        if (typeof process !== 'undefined') {
            console.log('\nPress Enter to continue...');
            await new Promise(resolve => {
                process.stdin.once('data', resolve);
            });
        }
    }

    console.log('\n✅ All examples completed!');
}

// Run examples if this file is executed directly
if (typeof require !== 'undefined' && require.main === module) {
    main().catch(console.error);
}

// Export for use as a module
if (typeof module !== 'undefined') {
    module.exports = {
        DRYAD.AIClient,
        basicChatExample,
        multiAgentExample,
        documentSearchExample,
        systemMonitoringExample,
        webSocketExample,
        errorHandlingExample
    };
}
