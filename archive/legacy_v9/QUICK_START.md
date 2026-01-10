# DRYAD.AI Quick Start Guide

Get up and running with document processing, chat, and AI-powered project proposals in minutes!

## 🎯 What You Can Do

✅ **Upload folders of documents** (PDF, DOCX, TXT, MD, CSV, images)  
✅ **Chat with your documents** using local LLM  
✅ **Generate AI-powered project proposals** with Google Gemini  
✅ **Use Web UI or CLI** - your choice!

## ⚡ 5-Minute Setup

### Option 1: Automated Setup (Recommended)

```powershell
# Run the automated setup script
.\start-full-stack.ps1
```

This will:
1. ✅ Check prerequisites (Docker, Python, Node.js)
2. ✅ Start Weaviate vector database
3. ✅ Initialize the database
4. ✅ Start backend server (port 8000)
5. ✅ Start frontend UI (port 3000)
6. ✅ Open browser to http://localhost:3000/writer

### Option 2: Manual Setup

```powershell
# 1. Start Weaviate
docker run -d -p 8080:8080 --name weaviate semitechnologies/weaviate:1.26.1

# 2. Initialize database
alembic upgrade head

# 3. Install Google Gemini package
pip install google-generativeai

# 4. Add Gemini API key to .env
# Get free key from: https://makersuite.google.com/app/apikey
# Add to .env: GEMINI_API_KEY="your-key-here"

# 5. Start backend (new terminal)
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 6. Start frontend (new terminal)
cd frontend/writer-portal
npm install
$env:NEXT_PUBLIC_API_BASE="http://localhost:8000"
npm run dev

# 7. Open browser
# http://localhost:3000/writer
```

## 🌐 Using the Web UI

### 1. Sign In
- Open http://localhost:3000/writer
- Click "Sign in with Google"

### 2. Upload Documents
- Drag and drop a folder onto the upload area
- Or click to select files/folders
- Supports: PDF, DOCX, TXT, MD, CSV, images

### 3. Chat with Documents
- Type a question in the "Ask Gremlins" section
- Get AI-powered answers with citations

### 4. Generate Project Proposal
- Scroll to "Generate Project Proposal"
- Select proposal type (General, Technical, Business, Research)
- Add focus areas (optional): e.g., "market analysis, competitive landscape"
- Click "Generate Proposal with Gemini AI"
- Wait 30-60 seconds for deep analysis
- Download or copy the generated proposal

## 💻 Using the CLI

### Quick Commands

```bash
# Upload a folder and generate proposal in ONE command
python cli/gremlins_cli.py proposal from-folder ./my-documents \
  --type business \
  --output proposal.md

# Upload documents
python cli/gremlins_cli.py document upload-folder ./my-documents

# Chat with documents
python cli/gremlins_cli.py document search "What are the key findings?" --rag

# Generate proposal
python cli/gremlins_cli.py proposal generate --type business --output proposal.md

# Interactive chat mode
python cli/gremlins_cli.py interactive
```

See [CLI_GUIDE.md](CLI_GUIDE.md) for complete CLI documentation.

## 🔑 Get Your Gemini API Key

1. Go to https://makersuite.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key
5. Add to `.env` file:
   ```env
   GEMINI_API_KEY="your-actual-key-here"
   ```
6. Restart the backend server

**Note:** Gemini API is free for moderate use!

## 📊 Example Workflow

### Scenario: Generate a Business Proposal

**Using Web UI:**
1. Sign in with Google
2. Upload your business documents folder
3. Go to "Generate Project Proposal"
4. Select "Business Case" type
5. Add focus: "market analysis, financial projections"
6. Click "Generate Proposal"
7. Download the markdown file

**Using CLI:**
```bash
python cli/gremlins_cli.py proposal from-folder ./business-docs \
  --type business \
  --focus "market analysis,financial projections" \
  --output business-proposal.md
```

## 🎨 Features

### Document Processing
- **Automatic parsing**: Extracts text from PDFs, DOCX, etc.
- **Chunking**: Splits documents into searchable chunks
- **Vector indexing**: Creates semantic embeddings for search
- **Background processing**: Handles large files without timeouts

### Chat Interface
- **RAG (Retrieval-Augmented Generation)**: Answers based on your documents
- **Citations**: Shows which documents were used
- **Context-aware**: Maintains conversation history
- **Local LLM**: Uses TinyLlama for privacy

### Project Proposal Generation
- **Deep Analysis**: Google Gemini 1.5 Pro analyzes all documents
- **Structured Output**: Executive summary, recommendations, timeline, risks
- **Customizable**: Choose type and focus areas
- **Professional**: 2000-3000 word comprehensive proposals

## 🔧 Troubleshooting

### Backend won't start
```powershell
# Check if port 8000 is in use
netstat -ano | findstr :8000

# Use different port if needed
python -m uvicorn app.main:app --reload --port 8001
```

### Weaviate not running
```powershell
# Check Docker
docker ps

# Start Weaviate
docker start weaviate

# Or create new container
docker run -d -p 8080:8080 --name weaviate semitechnologies/weaviate:1.26.1
```

### Proposal generation fails
```bash
# Check status
python cli/gremlins_cli.py proposal status

# Make sure GEMINI_API_KEY is in .env
# Restart backend after adding key
```

### Frontend won't start
```powershell
cd frontend/writer-portal
rm -r node_modules
npm install
npm run dev
```

## 📍 Access Points

- **Frontend UI**: http://localhost:3000/writer
- **API Docs**: http://localhost:8000/docs
- **Weaviate**: http://localhost:8080/v1/meta

## 📚 Documentation

- [SETUP_GUIDE.md](SETUP_GUIDE.md) - Detailed setup instructions
- [CLI_GUIDE.md](CLI_GUIDE.md) - Complete CLI reference
- [README.md](README.md) - Full system documentation

## 🎉 Success Checklist

- [ ] Backend running on port 8000
- [ ] Frontend running on port 3000
- [ ] Weaviate running on port 8080
- [ ] Can sign in with Google
- [ ] Can upload documents
- [ ] Can chat with documents
- [ ] Gemini API key configured
- [ ] Can generate project proposals

## 💡 Tips

1. **Start with small folders**: Test with 5-10 documents first
2. **Use specific focus areas**: Better focus = better proposals
3. **Try both UI and CLI**: Use what works best for your workflow
4. **Save proposals**: Always download/save generated proposals
5. **Check status first**: Run `proposal status` before generating

## 🚀 Next Steps

1. **Upload your first documents**
2. **Try the chat interface**
3. **Generate your first proposal**
4. **Explore the CLI commands**
5. **Customize for your needs**

## 🆘 Need Help?

- Check the [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed instructions
- Check the [CLI_GUIDE.md](CLI_GUIDE.md) for CLI commands
- View API docs at http://localhost:8000/docs
- Check backend logs in the terminal

---

**Ready to start?** Run `.\start-full-stack.ps1` and you'll be up in 5 minutes! 🎉

