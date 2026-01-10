# DRYAD.AI OAuth2 & JWT Authentication Tester

A comprehensive React/TypeScript frontend testing application specifically designed to validate OAuth2 and JWT authentication across all DRYAD.AI Backend capabilities.

## 🎯 Purpose

This application systematically tests every OAuth2/JWT-protected feature in the DRYAD.AI Backend, providing detailed validation of:

- **OAuth2 Google Authentication Flow** - End-to-end login/logout testing
- **JWT Token Management** - Token exchange, refresh, and expiration handling
- **REST API Authentication** - All 103+ protected endpoints validation
- **WebSocket Authentication** - Real-time communication with JWT tokens
- **GraphQL API Authentication** - Query and mutation authentication testing
- **Error Handling** - Invalid token scenarios and network failure recovery

## 🚀 Features

### Core Authentication Testing
- ✅ Google OAuth2 login/logout flow validation
- ✅ JWT token exchange from Google ID token
- ✅ Token storage, retrieval, and refresh mechanisms
- ✅ Token expiration and automatic refresh handling
- ✅ Token inspection and decoding utilities

### Comprehensive API Testing
- ✅ **REST API Endpoints** - All agent, document, multi-agent, multimodal, and orchestrator endpoints
- ✅ **WebSocket Communication** - Authentication via query parameter, connection handling
- ✅ **GraphQL Queries** - Schema introspection, user queries, mutations, subscriptions
- ✅ **Error Scenarios** - 401 responses, expired tokens, missing headers

### Real-time Testing
- ✅ WebSocket connection with JWT authentication
- ✅ Real-time message sending and receiving
- ✅ Connection handling with expired tokens
- ✅ Graceful disconnect and reconnection

### User Interface
- ✅ Modern React/TypeScript with Tailwind CSS
- ✅ Comprehensive test dashboard with pass/fail indicators
- ✅ JWT token inspector with detailed analysis
- ✅ Real-time test results and logging
- ✅ Responsive design with accessibility compliance

## 🛠 Technology Stack

- **Frontend**: React 18, TypeScript, Tailwind CSS
- **Authentication**: Google OAuth2, JWT tokens
- **HTTP Client**: Axios with interceptors
- **WebSocket**: Native WebSocket API
- **Icons**: Heroicons
- **Build Tool**: Create React App

## 📋 Prerequisites

- Node.js 16+ and npm/yarn
- DRYAD.AI Backend running on `http://localhost:8000`
- Google OAuth2 client credentials
- Modern web browser with JavaScript enabled

## 🔧 Installation & Setup

1. **Clone and Install Dependencies**
   ```bash
   cd frontend-auth-tester
   npm install
   ```

2. **Configure Environment Variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and set:
   ```env
   REACT_APP_GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
   REACT_APP_API_BASE_URL=http://localhost:8000
   REACT_APP_WS_BASE_URL=ws://localhost:8000
   ```

3. **Start the Application**
   ```bash
   npm start
   ```
   
   The application will open at `http://localhost:3000`

## 🧪 Testing Capabilities

### 1. Authentication Flow Testing
- **Google OAuth2 Login**: Complete flow from Google sign-in to JWT token receipt
- **Token Exchange**: Validation of Google ID token to DRYAD.AI JWT conversion
- **Token Refresh**: Automatic and manual token refresh testing
- **Logout**: Proper token cleanup and session termination

### 2. REST API Endpoint Testing
Tests all protected endpoints including:

- **Authentication Endpoints** (`/api/v1/auth/*`)
  - `/config` - OAuth2 configuration
  - `/me` - Current user information
  - `/verify` - Token validity check
  - `/refresh` - Token refresh

- **Agent Endpoints** (`/api/v1/agent/*`)
  - `/chat` - Agent conversation
  - `/status` - Agent system status

- **Document Endpoints** (`/api/v1/documents/*`)
  - `/` - Document listing
  - `/search` - Document search
  - `/upload` - File upload

- **Multi-Agent Endpoints** (`/api/v1/multi-agent/*`)
  - `/status` - Multi-agent system status
  - `/workflows` - Workflow management

- **Multimodal Endpoints** (`/api/v1/multimodal/*`)
  - `/status` - Multimodal processing status
  - `/search` - Cross-modal search

- **Real-time Endpoints** (`/api/v1/realtime/*`)
  - `/status` - Real-time system status

- **Health Endpoints** (`/api/v1/health/*`)
  - `/` - Basic health check
  - `/status` - Detailed system health

### 3. WebSocket Authentication Testing
- **Authenticated Connection**: Connection with valid JWT token via query parameter
- **Unauthenticated Access**: Verification that connections without tokens are rejected
- **Expired Token Handling**: Testing behavior with expired/invalid tokens
- **Message Exchange**: Sending and receiving messages over authenticated connections
- **Connection Lifecycle**: Connect, authenticate, communicate, disconnect testing

### 4. GraphQL Authentication Testing
- **Schema Introspection**: With and without authentication
- **User Queries**: Current user information retrieval
- **Document Queries**: User document access
- **Chat History**: Conversation history access
- **Mutations**: Document creation and updates
- **Subscriptions**: Real-time updates (if supported)
- **Error Handling**: Authentication failures and permission errors

## 📊 Test Results & Reporting

### Dashboard Features
- **Real-time Test Execution**: Live updates as tests run
- **Pass/Fail Indicators**: Clear visual status for each test
- **Response Time Tracking**: Performance metrics for each endpoint
- **Error Details**: Comprehensive error messages and debugging info
- **Test Categories**: Organized by REST, WebSocket, and GraphQL

### Token Inspector
- **JWT Decoding**: Complete token payload analysis
- **Expiration Tracking**: Real-time countdown to token expiry
- **Token Refresh**: Manual refresh capability with status feedback
- **Raw Token Display**: Full token inspection for debugging
- **User Information**: Decoded user details and permissions

## 🔍 Usage Instructions

### 1. Authentication
1. Open the application at `http://localhost:3000`
2. Click "Sign in with Google" button
3. Complete Google OAuth2 flow
4. Verify successful authentication and token receipt

### 2. Running Tests
1. **All Tests**: Click "Run All Tests" to execute comprehensive test suite
2. **Individual Categories**: Use tabs to run specific test types:
   - **REST API**: Test all HTTP endpoints
   - **WebSocket**: Test real-time communication
   - **GraphQL**: Test GraphQL queries and mutations

### 3. Analyzing Results
1. **Test Dashboard**: Review pass/fail status for each endpoint
2. **Response Details**: Click on test results for detailed information
3. **Token Inspector**: Analyze JWT token contents and validity
4. **Error Investigation**: Review error messages for failed tests

## 🚨 Error Scenarios Tested

### Authentication Errors
- Invalid Google OAuth2 tokens
- Expired JWT tokens
- Missing authentication headers
- Malformed authorization headers

### Network Errors
- Connection timeouts
- Server unavailability
- Network interruptions
- DNS resolution failures

### Permission Errors
- Insufficient user roles
- Missing permissions
- Resource access restrictions
- Rate limiting responses

## 🔧 Configuration Options

### Environment Variables
- `REACT_APP_GOOGLE_CLIENT_ID`: Google OAuth2 client ID
- `REACT_APP_API_BASE_URL`: DRYAD.AI Backend base URL
- `REACT_APP_WS_BASE_URL`: WebSocket server base URL
- `REACT_APP_TEST_TIMEOUT`: Test timeout in milliseconds
- `REACT_APP_TEST_RETRY_COUNT`: Number of test retries on failure

### Customization
- Modify `src/services/apiTestService.ts` to add new endpoints
- Update `src/services/websocketTestService.ts` for WebSocket test scenarios
- Extend `src/services/graphqlTestService.ts` for additional GraphQL queries

## 📝 Development Notes

### Architecture
- **Service Layer**: Separate services for auth, API testing, WebSocket, and GraphQL
- **Component Structure**: Modular React components with TypeScript
- **State Management**: React Context for authentication state
- **Error Handling**: Comprehensive error boundaries and user feedback

### Security Considerations
- Tokens stored in localStorage (consider httpOnly cookies for production)
- Automatic token refresh with fallback to re-authentication
- Secure WebSocket connections with token validation
- CORS handling for cross-origin requests

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add comprehensive tests for new functionality
4. Ensure all existing tests pass
5. Submit a pull request with detailed description

## 📄 License

This project is part of the DRYAD.AI Backend testing suite and follows the same licensing terms.

## 🆘 Troubleshooting

### Common Issues
1. **Google OAuth2 Setup**: Ensure client ID is correctly configured
2. **CORS Errors**: Verify backend CORS settings allow frontend origin
3. **WebSocket Connection**: Check firewall settings and WebSocket support
4. **Token Expiry**: Tokens expire after 1 hour by default

### Support
For issues related to the DRYAD.AI Backend, refer to the main project documentation and issue tracker.
