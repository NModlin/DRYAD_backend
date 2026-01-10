import React from 'react'
import { Brain, Search, Bell, User, Settings, LogOut } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'

const Header: React.FC = () => {
  const { user, logout } = useAuth()

  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        {/* Logo and Search */}
        <div className="flex items-center space-x-6">
          <div className="flex items-center space-x-2">
            <Brain className="w-8 h-8 text-primary-600" />
            <span className="text-xl font-bold text-gray-900">Dryads Console</span>
          </div>
          
          <div className="relative w-96">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search groves, branches, or memories..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>
        </div>

        {/* User Menu */}
        <div className="flex items-center space-x-4">
          <button className="relative p-2 text-gray-600 hover:text-gray-900 rounded-lg hover:bg-gray-100">
            <Bell className="w-5 h-5" />
            <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
          </button>
          
          <button className="p-2 text-gray-600 hover:text-gray-900 rounded-lg hover:bg-gray-100">
            <Settings className="w-5 h-5" />
          </button>

          <div className="relative group">
            <button className="flex items-center space-x-2 p-2 rounded-lg hover:bg-gray-100">
              <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
                <User className="w-4 h-4 text-primary-600" />
              </div>
              <span className="text-sm font-medium text-gray-700">{user?.name}</span>
            </button>
            
            {/* Dropdown Menu */}
            <div className="absolute right-0 top-full mt-2 w-48 bg-white rounded-lg shadow-large border border-gray-200 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50">
              <div className="p-2">
                <div className="px-3 py-2 text-sm text-gray-600 border-b border-gray-100">
                  {user?.email}
                </div>
                <button 
                  onClick={logout}
                  className="flex items-center space-x-2 w-full px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-md"
                >
                  <LogOut className="w-4 h-4" />
                  <span>Sign out</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}

export default Header