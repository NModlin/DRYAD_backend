"use client";
import React, { useEffect, useState } from 'react';
import FolderUploader from '@/components/FolderUploader';
import ProposalGenerator from '@/components/ProposalGenerator';
import { ragQuery } from '@/lib/api';
import { useAuth } from '@/components/AuthProvider';

export default function WriterPage() {
  const { user, login, logout, refreshAuth } = useAuth();
  const [query, setQuery] = useState('');
  const [answer, setAnswer] = useState<string>('');
  const [citations, setCitations] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Auto-prompt login if no user to streamline UX
    if (!user) {
      // Do not auto prompt to avoid intrusive popups; keep manual flow
    }
  }, [user]);

  const onAsk = async () => {
    if (!query.trim()) return;
    setLoading(true);
    try {
      const res = await ragQuery(query.trim());
      setAnswer(res.answer);
      setCitations(res.sources || []);
    } catch (e: any) {
      setAnswer(`Error: ${e?.message || 'RAG failed'}`);
      setCitations([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-bold text-gray-900">Writer's Workspace</h1>

      <section className="space-y-2">
        <h2 className="text-xl font-semibold">Upload your folder</h2>
        {!user ? (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm">
              <span className="text-gray-600">Please sign in with Google to upload and query your documents.</span>
              <button className="px-3 py-1 rounded bg-blue-600 text-white hover:bg-blue-700" onClick={login}>Sign in with Google</button>
            </div>
            <div className="text-xs text-gray-500">
              Having trouble signing in? Try refreshing the page or clearing your browser cache.
            </div>
          </div>
        ) : (
          <div className="flex items-center gap-3 text-sm">
            <span className="text-gray-700">Signed in as {user.name || user.email}</span>
            <button className="px-3 py-1 rounded border border-blue-300 text-blue-700 hover:bg-blue-50" onClick={refreshAuth}>Refresh Auth</button>
            <button className="px-3 py-1 rounded border" onClick={logout}>Logout</button>
          </div>
        )}
        <FolderUploader onBatchesComplete={(s) => console.log('Upload summary', s)} />
      </section>

      <section className="space-y-2">
        <h2 className="text-xl font-semibold">Ask Gremlins</h2>
        <div className="flex gap-2">
          <input
            className="flex-1 border rounded px-3 py-2"
            placeholder="Ask about your book materials…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button className="px-4 py-2 rounded bg-blue-600 text-white" onClick={onAsk} disabled={loading || !user}>
            {loading ? 'Thinking…' : 'Ask'}
          </button>
        </div>
        {!user && <div className="text-sm text-gray-600">Sign in to ask questions.</div>}
        {answer && (
          <div className="mt-3 space-y-2">
            <div className="whitespace-pre-wrap">{answer}</div>
            {citations.length > 0 && (
              <div className="text-sm">
                <div className="font-medium mb-1">Citations</div>
                <ul className="list-disc ml-6">
                  {citations.map((c, idx) => (
                    <li key={c.id || idx}>
                      {c.document_title || c.id} — score {typeof c.score === 'number' ? c.score.toFixed(3) : c.score}
                      {c.content && <div className="text-gray-600">{c.content.slice(0, 200)}…</div>}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </section>

      <section className="space-y-2">
        <h2 className="text-xl font-semibold">Generate Project Proposal</h2>
        <p className="text-sm text-gray-600">
          After uploading your documents, use Google Gemini AI to generate a comprehensive project proposal with deep research and analysis.
        </p>
        <ProposalGenerator />
      </section>
    </div>
  );
}

