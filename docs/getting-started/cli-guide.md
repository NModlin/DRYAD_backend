# DRYAD.AI CLI Guide

Complete command-line interface for document processing, chat, and AI-powered project proposal generation.

## 🚀 Quick Start

### Installation

The CLI is included with DRYAD.AI. Make sure you have the backend running:

```powershell
# Start the backend server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Configuration

Set up your CLI configuration:

```bash
# Set the API base URL (default: http://localhost:8000)
python cli/gremlins_cli.py config set base_url http://localhost:8000

# Set API key if using authentication
python cli/gremlins_cli.py config set api_key your-api-key-here

# View current configuration
python cli/gremlins_cli.py config show
```

## 📖 Commands Overview

### Document Management

#### Upload a Single Document
```bash
python cli/gremlins_cli.py document upload path/to/document.pdf
python cli/gremlins_cli.py document upload path/to/document.pdf --title "My Document"
```

#### Upload an Entire Folder
```bash
# Upload all supported files from a folder
python cli/gremlins_cli.py document upload-folder ./my-documents

# Upload recursively (including subdirectories)
python cli/gremlins_cli.py document upload-folder ./my-documents --recursive

# Upload only specific file types
python cli/gremlins_cli.py document upload-folder ./my-documents --extensions pdf,docx,txt
```

**Supported file types:** PDF, DOCX, DOC, TXT, MD, CSV, XLSX, XLS, JPG, JPEG, PNG

#### Search Documents
```bash
# Basic search
python cli/gremlins_cli.py document search "machine learning"

# Search with more results
python cli/gremlins_cli.py document search "AI applications" --limit 10

# Search with RAG (get AI-generated answer)
python cli/gremlins_cli.py document search "What are the key findings?" --rag
```

#### List Documents
```bash
# List all documents
python cli/gremlins_cli.py document list

# List with pagination
python cli/gremlins_cli.py document list --limit 20 --offset 0
```

### Project Proposal Generation (NEW!)

#### Check Proposal Service Status
```bash
python cli/gremlins_cli.py proposal status
```

This will show:
- ✅ Whether Gemini API is configured
- 🤖 Which AI model is being used
- ❌ Any configuration errors

#### Generate Proposal from Uploaded Documents
```bash
# Basic proposal generation
python cli/gremlins_cli.py proposal generate

# Specify proposal type
python cli/gremlins_cli.py proposal generate --type business

# Add focus areas
python cli/gremlins_cli.py proposal generate \
  --type technical \
  --focus "architecture,scalability,security"

# Add additional context
python cli/gremlins_cli.py proposal generate \
  --type business \
  --context "Focus on B2B SaaS market opportunities in healthcare"

# Save to file
python cli/gremlins_cli.py proposal generate \
  --type business \
  --output ./project-proposal.md
```

**Proposal Types:**
- `general` - General-purpose project proposal
- `technical` - Technical project with implementation details
- `business` - Business case and market analysis
- `research` - Research proposal with methodology

#### Upload Folder + Generate Proposal (One Command!)
```bash
# Upload documents and generate proposal in one step
python cli/gremlins_cli.py proposal from-folder ./my-documents

# With all options
python cli/gremlins_cli.py proposal from-folder ./my-documents \
  --type business \
  --focus "market analysis,competitive landscape" \
  --context "Focus on enterprise customers" \
  --output ./proposal.md \
  --recursive
```

This command will:
1. 📁 Upload all documents from the folder
2. 🤖 Analyze them with Google Gemini AI
3. 📝 Generate a comprehensive project proposal
4. 💾 Save it to a file (if --output specified)

### Chat Commands

#### Interactive Chat Mode
```bash
python cli/gremlins_cli.py interactive
```

This starts an interactive chat session where you can:
- Ask questions about your documents
- Get AI-powered responses
- See conversation history
- Type `exit` or `quit` to end

#### Single Chat Query
```bash
python cli/gremlins_cli.py chat "What are the main topics in my documents?"
```

### System Commands

#### Check System Health
```bash
python cli/gremlins_cli.py system health
```

Shows:
- Backend status
- Database connectivity
- Vector store status
- LLM availability

#### Get System Info
```bash
python cli/gremlins_cli.py system info
```

## 🎯 Common Workflows

### Workflow 1: Quick Document Analysis
```bash
# 1. Upload documents
python cli/gremlins_cli.py document upload-folder ./research-papers

# 2. Search for specific information
python cli/gremlins_cli.py document search "methodology" --rag

# 3. Generate a research proposal
python cli/gremlins_cli.py proposal generate --type research --output proposal.md
```

### Workflow 2: Business Proposal Generation
```bash
# One command to do everything
python cli/gremlins_cli.py proposal from-folder ./business-docs \
  --type business \
  --focus "market analysis,financial projections,competitive landscape" \
  --context "B2B SaaS startup targeting healthcare industry" \
  --output business-proposal.md
```

### Workflow 3: Technical Documentation Analysis
```bash
# 1. Upload technical docs recursively
python cli/gremlins_cli.py document upload-folder ./tech-docs --recursive

# 2. Interactive chat to explore
python cli/gremlins_cli.py interactive

# 3. Generate technical proposal
python cli/gremlins_cli.py proposal generate \
  --type technical \
  --focus "architecture,scalability,security,deployment" \
  --output technical-proposal.md
```

## 🔧 Advanced Usage

### Using with Authentication

If your backend requires authentication:

```bash
# Set your API key
python cli/gremlins_cli.py config set api_key your-jwt-token-here

# Or use environment variable
export GREMLINS_API_KEY=your-jwt-token-here
```

### Custom Backend URL

```bash
# For remote backend
python cli/gremlins_cli.py config set base_url https://api.example.com

# For different local port
python cli/gremlins_cli.py config set base_url http://localhost:8001
```

### Batch Processing with Scripts

Create a bash/PowerShell script for batch operations:

```powershell
# process-folders.ps1
$folders = @("./folder1", "./folder2", "./folder3")

foreach ($folder in $folders) {
    Write-Host "Processing $folder..."
    python cli/gremlins_cli.py proposal from-folder $folder `
        --type business `
        --output "$folder-proposal.md"
}
```

## 📊 Output Examples

### Proposal Generation Output
```
✅ Proposal generated successfully!

┌─ Proposal Metadata ─────────────────────────────┐
│ 📊 Documents Analyzed: 15                       │
│ 📝 Type: business                               │
│ 📏 Words: 2,847                                 │
│ 🤖 Model: gemini-1.5-pro                       │
│ 🕐 Generated: 2024-01-15T10:30:00Z             │
└─────────────────────────────────────────────────┘

💾 Proposal saved to: ./project-proposal.md
```

### Folder Upload Output
```
📁 Found 12 files to upload

⬆️  Uploading: document1.pdf...
   ✅ Uploaded: document1.pdf (245,678 bytes)
⬆️  Uploading: document2.docx...
   ✅ Uploaded: document2.docx (123,456 bytes)
...

📊 Upload Summary:
   ✅ Uploaded: 12
```

## 🆘 Troubleshooting

### "Connection refused" error
```bash
# Make sure backend is running
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### "Proposal service not available"
```bash
# Check if Gemini API key is configured
python cli/gremlins_cli.py proposal status

# Add API key to .env file
# GEMINI_API_KEY="your-key-here"
```

### "No documents found"
```bash
# Upload documents first
python cli/gremlins_cli.py document upload-folder ./my-docs

# Then generate proposal
python cli/gremlins_cli.py proposal generate
```

### Authentication errors
```bash
# Set API key in config
python cli/gremlins_cli.py config set api_key your-token

# Or check current config
python cli/gremlins_cli.py config show
```

## 💡 Tips & Best Practices

1. **Use `from-folder` for efficiency**: The `proposal from-folder` command does everything in one step
2. **Specify focus areas**: More specific focus areas lead to better proposals
3. **Save to files**: Always use `--output` to save proposals for later reference
4. **Use recursive uploads**: Include `--recursive` to process entire directory trees
5. **Check status first**: Run `proposal status` before generating to ensure Gemini is configured
6. **Batch processing**: Create scripts for processing multiple folders

## 🎉 Quick Reference

```bash
# Configuration
gremlins config set base_url <url>
gremlins config show

# Documents
gremlins document upload <file>
gremlins document upload-folder <folder> [--recursive]
gremlins document search <query> [--rag]
gremlins document list

# Proposals
gremlins proposal status
gremlins proposal generate [--type TYPE] [--focus AREAS] [--output FILE]
gremlins proposal from-folder <folder> [OPTIONS]

# Chat
gremlins chat <message>
gremlins interactive

# System
gremlins system health
gremlins system info
```

## 📚 Next Steps

- Try the interactive mode: `python cli/gremlins_cli.py interactive`
- Generate your first proposal: `python cli/gremlins_cli.py proposal from-folder ./docs`
- Explore the web UI: http://localhost:3000/writer

For more information, see the main [SETUP_GUIDE.md](SETUP_GUIDE.md)

