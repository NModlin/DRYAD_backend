"use client";
import React, { useEffect, useMemo, useState } from 'react';
import { DocumentItem, deleteDocument, getDocuments } from '@/lib/api';

export default function DocumentLibrary() {
  const [docs, setDocs] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [type, setType] = useState('');
  const [view, setView] = useState<'list'|'grid'>('list');
  const [sortKey, setSortKey] = useState<'title'|'created_at'|'file_size'|'content_type'>('created_at');
  const [sortDir, setSortDir] = useState<'asc'|'desc'>('desc');

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const res = await getDocuments({ limit: 200 });
        setDocs(res.documents);
        setError(null);
      } catch (e: any) {
        setError(e?.message || 'Failed to load documents');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const filtered = useMemo(() => {
    const text = search.trim().toLowerCase();
    const arr = docs.filter(d => 
      (!text || d.title?.toLowerCase().includes(text) || d.content?.toLowerCase().includes(text)) &&
      (!type || d.content_type === type)
    );
    const sorter = (a: DocumentItem, b: DocumentItem) => {
      const dir = sortDir === 'asc' ? 1 : -1;
      const va = (a as any)[sortKey] ?? '';
      const vb = (b as any)[sortKey] ?? '';
      if (sortKey === 'file_size') return dir * (((a.file_size ?? 0) as number) - ((b.file_size ?? 0) as number));
      return dir * String(va).localeCompare(String(vb));
    };
    return arr.sort(sorter);
  }, [docs, search, type, sortKey, sortDir]);

  const onDelete = async (id: string) => {
    if (!confirm('Delete this document?')) return;
    try {
      await deleteDocument(id);
      setDocs(prev => prev.filter(d => d.id !== id));
    } catch (e: any) {
      alert(e?.message || 'Failed to delete');
    }
  };

  const Toolbar = (
    <div className="flex flex-wrap gap-2 items-center">
      <input className="border rounded px-3 py-2" placeholder="Search…" value={search} onChange={e => setSearch(e.target.value)} />
      <select className="border rounded px-3 py-2" value={type} onChange={e => setType(e.target.value)}>
        <option value="">All types</option>
        <option value="text/plain">text/plain</option>
        <option value="text/markdown">text/markdown</option>
        <option value="application/pdf">application/pdf</option>
        <option value="application/json">application/json</option>
      </select>
      <select className="border rounded px-3 py-2" value={sortKey} onChange={e => setSortKey(e.target.value as any)}>
        <option value="created_at">Upload date</option>
        <option value="title">Filename/Title</option>
        <option value="file_size">File size</option>
        <option value="content_type">Type</option>
      </select>
      <select className="border rounded px-3 py-2" value={sortDir} onChange={e => setSortDir(e.target.value as any)}>
        <option value="desc">Desc</option>
        <option value="asc">Asc</option>
      </select>
      <div className="ml-auto flex gap-1">
        <button className={`px-3 py-2 rounded border ${view==='list'?'bg-gray-100':''}`} onClick={() => setView('list')}>List</button>
        <button className={`px-3 py-2 rounded border ${view==='grid'?'bg-gray-100':''}`} onClick={() => setView('grid')}>Grid</button>
      </div>
    </div>
  );

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Document Library</h1>
      {Toolbar}
      {loading && <div>Loading…</div>}
      {error && <div className="text-red-700">{error}</div>}

      {view === 'list' ? (
        <table className="w-full text-sm border">
          <thead className="bg-gray-100">
            <tr>
              <th className="text-left p-2">Title</th>
              <th className="text-left p-2">Type</th>
              <th className="text-left p-2">Size</th>
              <th className="text-left p-2">Uploaded</th>
              <th className="text-left p-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map(doc => (
              <tr key={doc.id} className="border-t">
                <td className="p-2">
                  <div className="font-medium">{doc.title}</div>
                  {doc.content && <div className="text-gray-600">{doc.content.slice(0, 120)}{doc.content.length>120?'…':''}</div>}
                </td>
                <td className="p-2">{doc.content_type}</td>
                <td className="p-2">{((doc.file_size ?? 0)/1024/1024).toFixed(2)} MB</td>
                <td className="p-2">{doc.created_at ? new Date(doc.created_at).toLocaleString() : ''}</td>
                <td className="p-2">
                  <div className="flex gap-2">
                    <button className="px-2 py-1 rounded border" onClick={() => alert(JSON.stringify(doc, null, 2))}>View</button>
                    <button className="px-2 py-1 rounded border" onClick={() => onDelete(doc.id)}>Delete</button>
                    {/* Re-process action could call analyze endpoint if available */}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '12px' }}>
          {filtered.map(doc => (
            <div key={doc.id} className="border rounded p-2">
              <div className="font-medium">{doc.title}</div>
              <div className="text-xs text-gray-600">{doc.content_type} • {((doc.file_size ?? 0)/1024/1024).toFixed(2)} MB</div>
              {doc.content && <div className="text-sm text-gray-700 mt-1">{doc.content.slice(0, 160)}{doc.content.length>160?'…':''}</div>}
              <div className="flex gap-2 mt-2">
                <button className="px-2 py-1 rounded border" onClick={() => alert(JSON.stringify(doc, null, 2))}>View</button>
                <button className="px-2 py-1 rounded border" onClick={() => onDelete(doc.id)}>Delete</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

