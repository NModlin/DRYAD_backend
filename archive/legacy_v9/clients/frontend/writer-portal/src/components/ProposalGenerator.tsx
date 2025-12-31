"use client";
import React, { useState } from 'react';
import { useAuth } from '@/components/AuthProvider';

type ProposalType = 'general' | 'technical' | 'business' | 'research';

interface ProposalContent {
  full_text: string;
  sections: Record<string, string>;
  word_count: number;
  char_count: number;
}

interface ProposalMetadata {
  documents_analyzed: number;
  total_documents: number;
  proposal_type: string;
  generated_at: string;
  model_used: string;
}

interface ProposalResponse {
  success: boolean;
  proposal: ProposalContent | null;
  metadata: ProposalMetadata | null;
  error?: string;
}

export default function ProposalGenerator() {
  const { user } = useAuth();
  const [proposalType, setProposalType] = useState<ProposalType>('general');
  const [focusAreas, setFocusAreas] = useState<string>('');
  const [additionalContext, setAdditionalContext] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [proposal, setProposal] = useState<ProposalContent | null>(null);
  const [metadata, setMetadata] = useState<ProposalMetadata | null>(null);
  const [error, setError] = useState<string>('');
  const [activeSection, setActiveSection] = useState<string>('full_text');

  const generateProposal = async () => {
    if (!user) {
      setError('Please sign in to generate proposals');
      return;
    }

    setLoading(true);
    setError('');
    setProposal(null);
    setMetadata(null);

    try {
      const apiBase = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
      const token = localStorage.getItem('access_token');

      if (!token) {
        throw new Error('No authentication token found. Please sign in again.');
      }

      // Parse focus areas (comma-separated)
      const focusAreasList = focusAreas
        .split(',')
        .map(area => area.trim())
        .filter(area => area.length > 0);

      const response = await fetch(`${apiBase}/api/v1/documents/proposal/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          proposal_type: proposalType,
          focus_areas: focusAreasList.length > 0 ? focusAreasList : null,
          additional_context: additionalContext || null
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      const data: ProposalResponse = await response.json();

      if (data.success && data.proposal) {
        setProposal(data.proposal);
        setMetadata(data.metadata);
      } else {
        throw new Error(data.error || 'Failed to generate proposal');
      }
    } catch (err: any) {
      console.error('Proposal generation error:', err);
      setError(err.message || 'Failed to generate proposal');
    } finally {
      setLoading(false);
    }
  };

  const downloadProposal = () => {
    if (!proposal) return;

    const blob = new Blob([proposal.full_text], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `project-proposal-${Date.now()}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const copyToClipboard = () => {
    if (!proposal) return;
    navigator.clipboard.writeText(proposal.full_text);
    alert('Proposal copied to clipboard!');
  };

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-2xl font-bold mb-4">Generate Project Proposal</h2>
        <p className="text-gray-600 mb-6">
          Use Google Gemini AI to analyze your uploaded documents and generate a comprehensive project proposal.
        </p>

        <div className="space-y-4">
          {/* Proposal Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Proposal Type
            </label>
            <select
              value={proposalType}
              onChange={(e) => setProposalType(e.target.value as ProposalType)}
              className="w-full border rounded px-3 py-2"
              disabled={loading}
            >
              <option value="general">General Purpose</option>
              <option value="technical">Technical Project</option>
              <option value="business">Business Case</option>
              <option value="research">Research Proposal</option>
            </select>
          </div>

          {/* Focus Areas */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Focus Areas (comma-separated, optional)
            </label>
            <input
              type="text"
              value={focusAreas}
              onChange={(e) => setFocusAreas(e.target.value)}
              placeholder="e.g., market analysis, competitive landscape, financial projections"
              className="w-full border rounded px-3 py-2"
              disabled={loading}
            />
          </div>

          {/* Additional Context */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Additional Context (optional)
            </label>
            <textarea
              value={additionalContext}
              onChange={(e) => setAdditionalContext(e.target.value)}
              placeholder="Provide any additional context or requirements for the proposal..."
              rows={3}
              className="w-full border rounded px-3 py-2"
              disabled={loading}
            />
          </div>

          {/* Generate Button */}
          <button
            onClick={generateProposal}
            disabled={loading || !user}
            className="w-full px-6 py-3 rounded bg-blue-600 text-white font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <span className="flex items-center justify-center">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Generating Proposal...
              </span>
            ) : (
              'Generate Proposal with Gemini AI'
            )}
          </button>

          {!user && (
            <p className="text-sm text-red-600">Please sign in to generate proposals</p>
          )}
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800 font-medium">Error</p>
          <p className="text-red-600 text-sm mt-1">{error}</p>
        </div>
      )}

      {/* Proposal Display */}
      {proposal && metadata && (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xl font-bold">Generated Proposal</h3>
            <div className="flex gap-2">
              <button
                onClick={copyToClipboard}
                className="px-4 py-2 rounded border border-gray-300 hover:bg-gray-50 text-sm"
              >
                Copy to Clipboard
              </button>
              <button
                onClick={downloadProposal}
                className="px-4 py-2 rounded bg-blue-600 text-white hover:bg-blue-700 text-sm"
              >
                Download Markdown
              </button>
            </div>
          </div>

          {/* Metadata */}
          <div className="bg-gray-50 rounded p-4 mb-4 text-sm">
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div>
                <span className="text-gray-600">Documents:</span>
                <span className="ml-2 font-medium">{metadata.documents_analyzed}</span>
              </div>
              <div>
                <span className="text-gray-600">Type:</span>
                <span className="ml-2 font-medium">{metadata.proposal_type}</span>
              </div>
              <div>
                <span className="text-gray-600">Words:</span>
                <span className="ml-2 font-medium">{proposal.word_count.toLocaleString()}</span>
              </div>
              <div>
                <span className="text-gray-600">Model:</span>
                <span className="ml-2 font-medium">{metadata.model_used}</span>
              </div>
              <div>
                <span className="text-gray-600">Generated:</span>
                <span className="ml-2 font-medium">{new Date(metadata.generated_at).toLocaleString()}</span>
              </div>
            </div>
          </div>

          {/* Section Tabs */}
          {Object.keys(proposal.sections).length > 0 && (
            <div className="border-b mb-4">
              <div className="flex gap-2 overflow-x-auto">
                <button
                  onClick={() => setActiveSection('full_text')}
                  className={`px-4 py-2 text-sm font-medium border-b-2 whitespace-nowrap ${
                    activeSection === 'full_text'
                      ? 'border-blue-600 text-blue-600'
                      : 'border-transparent text-gray-600 hover:text-gray-900'
                  }`}
                >
                  Full Proposal
                </button>
                {Object.keys(proposal.sections).map((section) => (
                  <button
                    key={section}
                    onClick={() => setActiveSection(section)}
                    className={`px-4 py-2 text-sm font-medium border-b-2 whitespace-nowrap ${
                      activeSection === section
                        ? 'border-blue-600 text-blue-600'
                        : 'border-transparent text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    {section.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Proposal Content */}
          <div className="prose max-w-none">
            <div className="whitespace-pre-wrap font-mono text-sm bg-gray-50 p-4 rounded overflow-auto max-h-[600px]">
              {activeSection === 'full_text'
                ? proposal.full_text
                : proposal.sections[activeSection] || 'Section not found'}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

