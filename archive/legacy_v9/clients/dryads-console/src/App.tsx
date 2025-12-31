import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { QueryClient, QueryClientProvider } from 'react-query'

// Components
import Layout from './components/Layout'
import ChatInterface from './pages/ChatInterface'
import Dashboard from './pages/Dashboard'
import GroveExplorer from './pages/GroveExplorer'
import OracleConsultation from './pages/OracleConsultation'
import MemoryKeeperPanel from './pages/MemoryKeeperPanel'
import DocumentViewer from './pages/DocumentViewer'
import FileManager from './pages/FileManager'
import Login from './pages/Login'

// Hooks
import { AuthProvider } from './hooks/useAuth'

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <Router>
          <div className="App">
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/" element={<Layout />}>
                <Route index element={<ChatInterface />} />
                <Route path="dashboard" element={<Dashboard />} />
                <Route path="groves" element={<GroveExplorer />} />
                <Route path="oracle" element={<OracleConsultation />} />
                <Route path="memory" element={<MemoryKeeperPanel />} />
                <Route path="documents" element={<DocumentViewer />} />
                <Route path="files" element={<FileManager />} />
              </Route>
            </Routes>
            <Toaster
              position="top-right"
              toastOptions={{
                duration: 4000,
                style: {
                  background: '#1f2937',
                  color: '#f9fafb',
                },
                success: {
                  style: {
                    background: '#059669',
                  },
                },
                error: {
                  style: {
                    background: '#dc2626',
                  },
                },
              }}
            />
          </div>
        </Router>
      </AuthProvider>
    </QueryClientProvider>
  )
}

export default App