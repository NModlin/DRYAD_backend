import * as React from 'react'
import { Provider } from 'react-redux'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { store } from './store/store'
import { Header } from './components/layout/Header'
import { AuthenticationProvider } from './providers/AuthenticationProvider'
import './index.css'

// Temporary components until full implementation
const LoginPage = () => (
  <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center transition-colors duration-200">
    <div className="max-w-md w-full bg-white dark:bg-gray-800 p-8 rounded-lg shadow-md transition-colors duration-200">
      <h1 className="text-2xl font-bold text-center mb-6 text-gray-900 dark:text-white">DRYAD University Login</h1>
      <p className="text-center text-gray-600 dark:text-gray-300">Authentication system coming soon...</p>
    </div>
  </div>
)

const DashboardPage = () => (
  <div className="p-6 transition-colors duration-200">
    <h1 className="text-3xl font-bold mb-6 text-gray-900 dark:text-white">DRYAD University Dashboard</h1>
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md transition-colors duration-200">
        <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">Welcome</h2>
        <p className="text-gray-600 dark:text-gray-300">Dashboard components under development...</p>
      </div>
    </div>
  </div>
)

const Layout = ({ children }: { children: React.ReactNode }) => (
  <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex flex-col transition-colors duration-200">
    <Header />
    <main className="flex-1">
      {children}
    </main>
  </div>
)

function App() {
  return (
    <Provider store={store}>
      <AuthenticationProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/dashboard" element={<Layout><DashboardPage /></Layout>} />
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </AuthenticationProvider>
    </Provider>
  )
}

export default App