# DRYAD.AI Full Stack Setup Guide

Complete guide to set up DRYAD.AI with document processing, chat, and AI-powered project proposal generation.

## 🎯 What You'll Get

- ✅ Document upload and parsing (PDF, DOCX, TXT, MD, CSV, images)
- ✅ Folder-based batch upload via web UI
- ✅ Chat with your documents using hybrid cloud/local LLM
- ✅ **NEW:** AI-powered project proposal generation using Google Gemini
- ✅ Real-time WebSocket updates
- ✅ Google OAuth2 authentication

## 📋 Prerequisites

- Python 3.11+
- Node.js 18+ and npm
- Docker Desktop (for Weaviate vector database)
- Google Gemini API key (free at https://makersuite.google.com/app/apikey)

## 🚀 Quick Start (15 minutes)

### Step 1: Install Backend Dependencies

```powershell
# Make sure you're in the project root
cd C:\Users\nmodlin.RPL\OneDrive - Rehrig Pacific Company\Documents\GitHub\DRYAD_backend

# Activate virtual environment (if not already active)
.venv\Scripts\activate

# Install new dependencies (includes google-generativeai)
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables

Edit your `.env` file and add your Google Gemini API key:

```env
# Get your free API key from: https://makersuite.google.com/app/apikey
GEMINI_API_KEY="your-actual-gemini-api-key-here"
GEMINI_MODEL="gemini-1.5-pro"

# Hybrid LLM Configuration (Optional - for enhanced performance)
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
OLLAMA_CLOUD_URL=https://ollama.com
OLLAMA_CLOUD_ENABLED=true
OLLAMA_API_KEY=your_ollama_api_key_here
```

**To get your Gemini API key:**
1. Go to https://makersuite.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key and paste it in your `.env` file

**For enhanced LLM performance (Optional):**
1. Get Ollama Cloud access at https://ollama.com
2. Install local Ollama from https://ollama.ai/
3. See [Hybrid LLM Guide](../HYBRID_LLM_GUIDE.md) for detailed setup

### Step 3: Start Weaviate (Vector Database)

```powershell
# Start Weaviate in Docker
docker run -d -p 8080:8080 --name weaviate semitechnologies/weaviate:1.26.1

# Verify it's running
docker ps
```

### Step 4: Initialize Database

```powershell
# Run database migrations
alembic upgrade head
```

### Step 5: Start Backend Server

```powershell
# Start the FastAPI backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
```

**Keep this terminal open!** The backend is now running.

### Step 6: Setup Frontend (New Terminal)

Open a **new PowerShell terminal** and run:

```powershell
# Navigate to frontend
cd C:\Users\nmodlin.RPL\OneDrive - Rehrig Pacific Company\Documents\GitHub\DRYAD_backend\frontend\writer-portal

# Install dependencies (first time only)
npm install

# Set API base URL
$env:NEXT_PUBLIC_API_BASE="http://localhost:8000"

# Start frontend development server
npm run dev
```

You should see:
```
- ready started server on 0.0.0.0:3000, url: http://localhost:3000
```

### Step 7: Access the Application

Open your browser and go to:
- **Frontend UI:** http://localhost:3000/writer
- **API Documentation:** http://localhost:8000/docs

## 📖 How to Use

### 1. Sign In
- Click "Sign in with Google" on the Writer page
- Authenticate with your Google account

### 2. Upload Documents
- Click the upload area or drag-and-drop a folder
- Supports: PDF, DOCX, TXT, MD, CSV, images
- Files are automatically parsed and indexed

### 3. Chat with Documents
- Type a question in the "Ask Gremlins" section
- Get AI-powered answers with citations from your documents

### 4. Generate Project Proposal (NEW!)
- Scroll to "Generate Project Proposal" section
- Select proposal type (General, Technical, Business, Research)
- Optionally add focus areas (e.g., "market analysis, competitive landscape")
- Click "Generate Proposal with Gemini AI"
- Wait 30-60 seconds for deep analysis
- Download or copy the generated proposal

## 🔧 Troubleshooting

### Backend won't start
```powershell
# Check if port 8000 is already in use
netstat -ano | findstr :8000

# If something is using it, kill the process or use a different port
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

### Weaviate connection error
```powershell
# Check if Weaviate is running
docker ps

# If not running, start it
docker start weaviate

# If container doesn't exist, create it
docker run -d -p 8080:8080 --name weaviate semitechnologies/weaviate:1.26.1
```

### Frontend won't start
```powershell
# Clear npm cache and reinstall
cd frontend\writer-portal
rm -r node_modules
rm package-lock.json
npm install
npm run dev
```

### Proposal generation fails
- **Error: "Gemini API not configured"**
  - Make sure you added `GEMINI_API_KEY` to `.env`
  - Restart the backend server after adding the key
  
- **Error: "No documents found"**
  - Upload some documents first before generating a proposal
  
- **Error: "API key invalid"**
  - Verify your API key at https://makersuite.google.com/app/apikey
  - Make sure there are no extra spaces in the `.env` file

### Authentication issues
- Clear browser cookies and local storage
- Try incognito/private browsing mode
- Check that Google OAuth credentials are correct in `.env`

## 🎨 Features Overview

### Document Processing
- **Supported formats:** PDF, DOCX, TXT, MD, CSV, XLS, XLSX, images
- **Automatic chunking:** Text split into 1000-char chunks with 200-char overlap
- **Vector indexing:** Semantic embeddings stored in Weaviate
- **Background processing:** Large files processed asynchronously

### Chat Interface
- **Context-aware:** Uses RAG (Retrieval-Augmented Generation)
- **Citations:** Shows which documents were used for answers
- **Conversation history:** Maintains chat context
- **Hybrid LLM:** Intelligent routing between cloud and local models for optimal performance

### Project Proposal Generation
- **AI Model:** Google Gemini 1.5 Pro (1M token context)
- **Deep Analysis:** Analyzes all uploaded documents comprehensively
- **Structured Output:** Executive summary, recommendations, timeline, risks, etc.
- **Customizable:** Choose proposal type and focus areas
- **Export:** Download as Markdown or copy to clipboard

## 📊 API Endpoints

### Documents
- `POST /api/v1/documents/upload` - Upload single file
- `POST /api/v1/documents/upload/batch` - Upload multiple files
- `POST /api/v1/documents/rag` - Query documents with RAG
- `GET /api/v1/documents` - List all documents

### Proposals (NEW!)
- `GET /api/v1/documents/proposal/status` - Check if Gemini is configured
- `POST /api/v1/documents/proposal/generate` - Generate project proposal

### Authentication
- `POST /api/v1/auth/google` - Google OAuth2 login
- `POST /api/v1/auth/refresh` - Refresh access token

## 🔐 Security Notes

- **API Keys:** Never commit `.env` file to version control
- **OAuth2:** Uses secure JWT tokens with expiration
- **File Validation:** Strict file type and size limits
- **Virus Scanning:** Optional ClamAV integration available

## 📈 Next Steps

1. **Upload your documents** - Start with a small folder (5-10 files)
2. **Test chat** - Ask questions about your documents
3. **Generate proposal** - Create your first AI-powered proposal
4. **Customize** - Adjust proposal types and focus areas for your needs

## 🆘 Need Help?

- **API Documentation:** http://localhost:8000/docs
- **Check logs:** Backend terminal shows detailed error messages
- **Test endpoints:** Use the Swagger UI at /docs to test API directly

## 🎉 Success Checklist

- [ ] Backend running on port 8000
- [ ] Frontend running on port 3000
- [ ] Weaviate running on port 8080
- [ ] Can sign in with Google
- [ ] Can upload documents
- [ ] Can chat with documents
- [ ] Can generate project proposals
- [ ] Gemini API key configured

If all items are checked, you're ready to go! 🚀

