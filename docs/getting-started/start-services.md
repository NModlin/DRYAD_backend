# Start DRYAD.AI Services - Step by Step

Follow these steps in order to start all services.

## Step 1: Start Weaviate (Vector Database)

Open PowerShell and run:

```powershell
docker start weaviate
```

If you get an error "No such container", create it first:

```powershell
docker run -d -p 8080:8080 --name weaviate semitechnologies/weaviate:1.26.1
```

**Verify:** Open http://localhost:8080/v1/meta in your browser (should show JSON)

---

## Step 2: Start Backend Server

Open a **NEW PowerShell terminal** and run:

```powershell
cd "C:\Users\nmodlin.RPL\OneDrive - Rehrig Pacific Company\Documents\GitHub\DRYAD_backend"
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or use the script:

```powershell
.\start-backend.ps1
```

**You should see:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
```

**Verify:** Open http://localhost:8000/docs in your browser (should show API docs)

**Keep this terminal open!**

---

## Step 3: Start Frontend Server

Open a **NEW PowerShell terminal** (3rd terminal) and run:

```powershell
cd "C:\Users\nmodlin.RPL\OneDrive - Rehrig Pacific Company\Documents\GitHub\DRYAD_backend\frontend\writer-portal"
$env:NEXT_PUBLIC_API_BASE = "http://localhost:8000"
npm run dev
```

Or use the script:

```powershell
cd "C:\Users\nmodlin.RPL\OneDrive - Rehrig Pacific Company\Documents\GitHub\DRYAD_backend"
.\start-frontend.ps1
```

**You should see:**
```
- ready started server on 0.0.0.0:3000, url: http://localhost:3000
```

**Verify:** Open http://localhost:3000/writer in your browser

**Keep this terminal open!**

---

## Step 4: Access the Application

Open your browser to: **http://localhost:3000/writer**

You should see:
- Sign in with Google button
- Upload area for documents
- Chat interface
- Proposal generator

---

## Quick Verification Commands

Run these in a new PowerShell to verify all services:

```powershell
# Check Weaviate
curl http://localhost:8080/v1/meta

# Check Backend
curl http://localhost:8000/api/v1/health/status

# Check Frontend
curl http://localhost:3000
```

All three should return responses (not connection errors).

---

## Troubleshooting

### Weaviate won't start
```powershell
# Remove old container and create new one
docker rm -f weaviate
docker run -d -p 8080:8080 --name weaviate semitechnologies/weaviate:1.26.1

# Wait 5 seconds
Start-Sleep -Seconds 5

# Check if running
docker ps
```

### Backend won't start
```powershell
# Check if port 8000 is in use
netstat -ano | findstr :8000

# If something is using it, kill the process or use different port
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

### Frontend won't start
```powershell
# Check if port 3000 is in use
netstat -ano | findstr :3000

# Reinstall dependencies
cd frontend\writer-portal
rm -r node_modules
npm install
npm run dev
```

### "Module not found" errors
```powershell
# Make sure virtual environment is activated
.\.venv\Scripts\Activate.ps1

# Reinstall dependencies
pip install -r requirements.txt
```

---

## Summary

You need **3 terminals running simultaneously**:

1. **Terminal 1**: Weaviate (Docker container - runs in background)
2. **Terminal 2**: Backend (Python/FastAPI)
3. **Terminal 3**: Frontend (Next.js)

All three must be running for the system to work!

---

## Test the Complete System

Once all services are running:

1. Go to http://localhost:3000/writer
2. Sign in with Google
3. Upload a test document
4. Try the chat: "What is this document about?"
5. Generate a proposal:
   - Select "Business Case" type
   - Add focus: "market analysis"
   - Click "Generate Proposal"
   - Wait 30-60 seconds
   - Download the result

---

## Stop All Services

When you're done:

```powershell
# Stop Weaviate
docker stop weaviate

# Stop Backend - Press CTRL+C in Terminal 2

# Stop Frontend - Press CTRL+C in Terminal 3
```

