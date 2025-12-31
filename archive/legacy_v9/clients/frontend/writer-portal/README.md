# Gremlins Writer Portal (Next.js)

A writer-friendly UI to upload entire folders of documents and ask RAG questions with citations against the DRYAD.AI Backend.

## Backend endpoints wired

- Upload single: POST /api/v1/documents/upload (multipart form: file, metadata?)
- Upload batch: POST /api/v1/documents/upload/batch (multipart form: files[], metadata?)
- RAG query: POST /api/v1/documents/rag (JSON body)
- Real-time WS: ws://<API_BASE>/api/v1/realtime-ws/ws/{session_id}

Auth: If your backend enforces auth (it likely does), paste a Bearer token in the Writer page input. Token is forwarded via Authorization header.

## Run locally

1. cd frontend/writer-portal
2. npm install
3. set NEXT_PUBLIC_API_BASE=http://localhost:8000 (Windows PowerShell: $env:NEXT_PUBLIC_API_BASE="http://localhost:8000")
4. npm run dev
5. Open http://localhost:3000 and click "Open Writer Workspace"

## Notes

- Folder selection uses webkitdirectory (Chromium/Safari). On unsupported browsers, select multiple files manually or drag-and-drop the folder contents.
- Client batches uploads to ~50MB per batch with concurrency 3.
- WS is connected for potential per-file progress; backend provides events on /api/v1/realtime-ws.

## TODO

- OAuth2 Google login flow and token management
- Display per-file upload status and errors inline
- Document library view with previews and filters

