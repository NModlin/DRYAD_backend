"use client";
import React, { useCallback, useMemo, useRef, useState } from 'react';
import { uploadRealtimeXHR, connectUploadWebSocket } from '@/lib/api';
import { useAuth } from '@/components/AuthProvider';


type FileState = {
  file: File;
  id: string; // also used as upload_id for WS mapping
  status: 'queued' | 'uploading' | 'completed' | 'failed' | 'canceled';
  progress: number; // 0-100
  attempts: number;
  error?: string;
  speedBps?: number;
  etaSeconds?: number | null;
};

type Props = {
  onBatchesComplete?: (summary: { total: number; ok: number; failed: number }) => void;
};

export default function FolderUploader({ onBatchesComplete }: Props) {
  const { user, login } = useAuth();
  const inputRef = useRef<HTMLInputElement>(null);
  const [files, setFiles] = useState<FileState[]>([]);
  const [status, setStatus] = useState<'idle'|'uploading'|'done'|'error'>('idle');
  const [wsStatus, setWsStatus] = useState<string>('');
  const controllerRef = useRef<AbortController | null>(null);

  const onPick = () => {
    if (!user) { alert('Please sign in to upload documents.'); return; }
    inputRef.current?.click();
  };

  const onFilesChosen = useCallback((fl: FileList | null) => {
    if (!fl) return;
    const arr = Array.from(fl).filter(f => f.size > 0);
    setFiles(arr.map((f) => ({ file: f, id: crypto.randomUUID(), status: 'queued', progress: 0, attempts: 0 })));
    setStatus('idle');
  }, []);

  const onDrop: React.DragEventHandler<HTMLDivElement> = (e) => {
    e.preventDefault();
    const items = e.dataTransfer.items;
    const fs: File[] = [];
    if (items) {
      for (const item of Array.from(items as unknown as DataTransferItemList)) {
        const f = (item as DataTransferItem).kind === 'file' ? (item as DataTransferItem).getAsFile() : null;
        if (f) fs.push(f);
      }
    } else {
      fs.push(...Array.from(e.dataTransfer.files));
    }
    setFiles(fs.map((f) => ({ file: f, id: crypto.randomUUID(), status: 'queued', progress: 0, attempts: 0 })));
  };

  const cancelAll = useCallback(() => {
    controllerRef.current?.abort();
    controllerRef.current = null;
    setFiles(prev => prev.map(f => (f.status === 'uploading' ? { ...f, status: 'canceled', error: 'Canceled by user' } : f)));
    setStatus('idle');
  }, []);

  const retryFile = useCallback((id: string) => {
    setFiles(prev => prev.map(f => (f.id === id ? { ...f, status: 'queued', progress: 0, error: undefined } : f)));
  }, []);

  const startUpload = useCallback(async () => {
    if (!files.length) return;
    if (!user) {
      alert('Please sign in with Google to upload documents.');
      return;
    }

    setStatus('uploading');

    const sessionId = `writer-${Math.random().toString(36).slice(2)}`;
    let ws: WebSocket | null = null;
    try {
      ws = connectUploadWebSocket(sessionId);
      ws.onopen = () => setWsStatus('WebSocket connected');
      ws.onmessage = (ev) => {
        try {
          const msg = JSON.parse(ev.data);
          if (msg.type === 'upload_progress' && msg.upload_id && msg.progress) {
            setFiles(prev => prev.map(f => {
              if (f.id !== msg.upload_id) return f;
              const p = msg.progress.progress_percent ?? 0;
              const uploaded = msg.progress.uploaded_size ?? 0;
              const total = msg.progress.total_size ?? f.file.size;
              const remaining = Math.max(total - uploaded, 0);
              const speed = f.speedBps ?? 0;
              const eta = speed > 0 ? Math.round(remaining / speed) : null;
              return { ...f, progress: p, status: 'uploading', etaSeconds: eta };
            }));
          }
          if (msg.type === 'task_completed' && msg.result?.task_type === 'upload') {
            const uploadId = msg.task_id;
            if (uploadId) {
              setFiles(prev => prev.map(f => f.id === uploadId ? { ...f, status: 'completed', progress: 100, etaSeconds: 0 } : f));
            }
          }
        } catch {}
      };
      ws.onerror = () => setWsStatus('WebSocket error');
      ws.onclose = () => setWsStatus('');
    } catch {}

    const ac = new AbortController();
    controllerRef.current = ac;

    let ok = 0, failed = 0;
    const total = files.length;

    const uploadWithBackoff = async (idx: number) => {
      const maxAttempts = 3;
      let attempt = 0;
      while (attempt < maxAttempts && !ac.signal.aborted) {
        attempt++;
        try {
          const uploadId = files[idx].id; // tie frontend id as upload_id
          setFiles(prev => prev.map((f, i) => i === idx ? { ...f, status: 'uploading', attempts: attempt } : f));
          await uploadRealtimeXHR(files[idx].file, sessionId, (loaded, totalBytes, speed) => {
            setFiles(prev => prev.map((f, i) => {
              if (i !== idx) return f;
              const percent = totalBytes > 0 ? Math.round((loaded / totalBytes) * 100) : 0;
              const remaining = Math.max(totalBytes - loaded, 0);
              const eta = speed > 0 ? Math.round(remaining / speed) : null;
              return { ...f, progress: percent, speedBps: speed, etaSeconds: eta };
            }));
          }, { upload_id: uploadId });
          setFiles(prev => prev.map((f, i) => i === idx ? { ...f, status: 'completed', progress: 100, etaSeconds: 0 } : f));
          ok += 1;
          return;
        } catch (e: any) {
          const isLast = attempt >= maxAttempts;
          let errorMessage = 'Upload failed';

          // Parse user-friendly error messages
          if (e?.message?.includes('Authentication required')) {
            errorMessage = 'Please sign in to upload';
          } else if (e?.message?.includes('Network error')) {
            errorMessage = 'Network error - check connection';
          } else if (e?.message) {
            errorMessage = e.message;
          }

          setFiles(prev => prev.map((f, i) => i === idx ? { ...f, status: isLast ? 'failed' : 'queued', error: errorMessage } : f));
          if (isLast) { failed += 1; break; }
          await new Promise(r => setTimeout(r, 500 * attempt));
        }
      }
    };

    try {
      const concurrency = 3;
      let index = 0;
      const workers = Array.from({ length: Math.min(concurrency, total) }, () => (async () => {
        while (!ac.signal.aborted) {
          const i = index++;
          if (i >= total) break;
          if (files[i].status === 'canceled') continue;
          await uploadWithBackoff(i);
        }
      })());

      await Promise.all(workers);
      setStatus('done');
      onBatchesComplete?.({ total, ok, failed });
    } catch {
      setStatus('error');
    } finally {
      ws?.close();
      controllerRef.current = null;
    }
  }, [files, onBatchesComplete]);

  const overall = useMemo(() => {
    const completed = files.filter(f => f.status === 'completed').length;
    const failed = files.filter(f => f.status === 'failed').length;
    const uploading = files.filter(f => f.status === 'uploading').length;
    return { completed, failed, uploading, total: files.length };
  }, [files]);

  return (
    <div className="space-y-3">
      {!user && (
        <div className="bg-yellow-50 border border-yellow-200 rounded p-3 text-sm">
          <div className="text-yellow-800">
            <strong>Authentication required:</strong> Please sign in with Google to upload documents.
          </div>
          <div className="mt-2 flex gap-2">
            <button
              onClick={login}
              className="px-3 py-1 rounded bg-blue-600 text-white text-xs hover:bg-blue-700"
            >
              Sign in with Google
            </button>
            <button
              onClick={() => window.location.reload()}
              className="px-3 py-1 rounded border border-gray-300 text-gray-700 text-xs hover:bg-gray-50"
            >
              Refresh Page
            </button>
          </div>
        </div>
      )}

      <div
        onClick={onPick}
        onDragOver={(e) => { e.preventDefault(); e.dataTransfer.dropEffect = 'copy'; }}
        onDrop={onDrop}
        className={`rounded border-2 border-dashed p-6 text-center ${user ? 'cursor-pointer hover:bg-gray-50' : 'cursor-not-allowed bg-gray-100 opacity-60'}`}
      >
        <div><strong>{user ? 'Drop your book folder here' : 'Sign in to upload files'}</strong> {user && 'or click to select'}</div>
        <div className="text-sm text-gray-500">{user ? 'PDF, DOCX, MD, TXT, images, etc.' : 'Authentication required for document uploads'}</div>
      </div>

      <input
        ref={inputRef}
        type="file"
        multiple
        // @ts-ignore Chromium folder selection
        webkitdirectory="true"
        directory=""
        className="hidden"
        onChange={(e) => onFilesChosen(e.target.files)}
      />

      {files.length > 0 && (
        <div className="text-sm text-gray-700">Selected: {files.length} files</div>
      )}

      <div className="flex gap-2">
        <button onClick={startUpload} disabled={status==='uploading' || !user} className="px-4 py-2 rounded bg-blue-600 text-white disabled:opacity-50">
          {status === 'uploading' ? 'Uploading…' : 'Start upload'}
        </button>
        {!user && <button onClick={login} className="px-3 py-2 rounded border bg-blue-50 border-blue-300 text-blue-700 hover:bg-blue-100">Sign in with Google</button>}
        {status==='uploading' && (
          <button onClick={cancelAll} className="px-3 py-2 rounded border">Cancel</button>
        )}
        {wsStatus && <span className="text-xs text-gray-500">{wsStatus}</span>}
      </div>

      {files.length > 0 && (
        <div className="space-y-2">
          <div className="text-sm">Overall: {overall.completed} completed, {overall.failed} failed, {overall.uploading} uploading, {overall.total} total</div>
          <ul className="space-y-1">
            {files.map((f) => (
              <li key={f.id} className="border rounded p-2 text-sm flex items-center justify-between">
                <div>
                  <div><strong>{f.file.name}</strong> <span className="text-gray-500">({(f.file.size/1024/1024).toFixed(2)} MB)</span></div>
                  <div className="text-gray-600">Status: {f.status}{f.attempts > 1 ? ` (attempt ${f.attempts})` : ''}</div>
                  {typeof f.etaSeconds === 'number' && f.status==='uploading' && (
                    <div className="text-gray-600">ETA: {f.etaSeconds}s</div>
                  )}
                  {f.error && <div className="text-red-700">{f.error}</div>}
                </div>
                <div className="w-48">
                  <div className="h-2 bg-gray-200 rounded">
                    <div className="h-2 bg-blue-600 rounded" style={{ width: `${f.progress}%` }} />
                  </div>
                  {f.status === 'failed' && (
                    <button className="mt-1 px-2 py-1 rounded border" onClick={() => retryFile(f.id)}>Retry</button>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

