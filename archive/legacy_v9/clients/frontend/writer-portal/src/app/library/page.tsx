"use client";
import React, { useEffect, useMemo, useState } from 'react';
import { DocumentItem, getDocuments } from '@/lib/api';

export default function LibraryPage() {
  const [docs, setDocs] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('');

  const filtered = useMemo(() => {
    return docs.filter(d => 
      (!query || (d.title?.toLowerCase().includes(query.toLowerCase()) || d.content?.toLowerCase().includes(query.toLowerCase()))) &&
      (!typeFilter || d.content_type === typeFilter)
    );
  }, [docs, query, typeFilter]);

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const res = await getDocuments({ limit: 100 });
        setDocs(res.documents);
        setError(null);
      } catch (e: any) {
        setError(e?.message || 'Failed to load documents');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Your Documents</h1>

      <div className="flex gap-2">
        <input className="border rounded px-3 py-2 flex-1" placeholder="Search by title or content…" value={query} onChange={(e) => setQuery(e.target.value)} />
        <select className="border rounded px-3 py-2" value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}>
          <option value="">All types</option>
          <option value="text/plain">text/plain</option>
          <option value="text/markdown">text/markdown</option>
          <option value="application/pdf">application/pdf</option>
          <option value="application/json">application/json</option>
        </select>
      </div>

      {loading && <div>Loading…</div>}
      {error && <div className="text-red-700">{error}</div>}

      <ul className="space-y-2">
        {filtered.map(doc => (
          <li key={doc.id} className="border rounded p-3">
            <div className="flex items-center justify-between">
              <div className="font-medium">{doc.title}</div>
              <div className="text-sm text-gray-600">{doc.content_type} • {(doc.file_size ?? 0)/1024/1024 > 0 ? `${((doc.file_size ?? 0)/1024/1024).toFixed(2)} MB` : `${doc.content?.length ?? 0} chars`}</div>
            </div>
            {doc.content && <div className="text-sm text-gray-700 mt-1">{doc.content.slice(0, 240)}{doc.content.length > 240 ? '…' : ''}</div>}
            {doc.doc_metadata?.original_filename && <div className="text-xs text-gray-500 mt-1">{doc.doc_metadata.original_filename}</div>}
          </li>
        ))}
      </ul>
    </div>
  );
}

