import React from 'react'
import { useAuth } from '../../providers/AuthenticationProvider'

export const Header: React.FC = () => {
  const { user, logout } = useAuth()

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="px-6 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <h1 className="text-xl font-semibold text-gray-900">
            DRYAD University System
          </h1>
          {user && (
            <span className="text-sm text-gray-600">
              Welcome, {user.firstName} {user.lastName}
            </span>
          )}
        </div>

        {user && (
          <div className="flex items-center space-x-4">
            <button
              onClick={logout}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
            >
              Logout
            </button>
          </div>
        )}
      </div>
    </header>
  )
}