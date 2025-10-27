import React from 'react'
import { NavLink } from 'react-router-dom'
import { 
  Home, 
  TreePine, 
  Brain, 
  BookOpen, 
  Folder, 
  Users,
  Settings,
  Zap,
  MessageSquare,
  FileText
} from 'lucide-react'

const Sidebar: React.FC = () => {
  const navigation = [
    { name: 'Chat Interface', href: '/', icon: MessageSquare },
    { name: 'Dashboard', href: '/dashboard', icon: Home },
    { name: 'Grove Explorer', href: '/groves', icon: TreePine },
    { name: 'Oracle Consultation', href: '/oracle', icon: Brain },
    { name: 'Memory Keeper', href: '/memory', icon: BookOpen },
    { name: 'Document Viewer', href: '/documents', icon: FileText },
    { name: 'File Manager', href: '/files', icon: Folder },
  ]

  const memoryKeepers = [
    { name: 'Primary Keeper', status: 'active', avatar: '🧠' },
    { name: 'Research Keeper', status: 'active', avatar: '📚' },
    { name: 'Archive Keeper', status: 'idle', avatar: '🗄️' },
  ]

  return (
    <aside className="w-64 bg-white border-r border-gray-200 flex flex-col">
      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-2">
        {navigation.map((item) => (
          <NavLink
            key={item.name}
            to={item.href}
            className={({ isActive }) =>
              `flex items-center space-x-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-primary-50 text-primary-700 border-r-2 border-primary-600'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
              }`
            }
          >
            <item.icon className="w-4 h-4" />
            <span>{item.name}</span>
          </NavLink>
        ))}
      </nav>

      {/* Memory Keepers Section */}
      <div className="p-4 border-t border-gray-200">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
            Memory Keepers
          </h3>
          <Zap className="w-3 h-3 text-gray-400" />
        </div>
        
        <div className="space-y-2">
          {memoryKeepers.map((keeper) => (
            <div
              key={keeper.name}
              className="flex items-center space-x-2 p-2 rounded-lg bg-gray-50 hover:bg-gray-100 cursor-pointer transition-colors"
            >
              <span className="text-lg">{keeper.avatar}</span>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {keeper.name}
                </p>
                <div className="flex items-center space-x-1">
                  <div
                    className={`w-2 h-2 rounded-full ${
                      keeper.status === 'active' ? 'bg-success-500' : 'bg-gray-400'
                    }`}
                  />
                  <span className="text-xs text-gray-500 capitalize">
                    {keeper.status}
                  </span>
                </div>
              </div>
              <MessageSquare className="w-3 h-3 text-gray-400" />
            </div>
          ))}
        </div>
      </div>

      {/* System Status */}
      <div className="p-4 border-t border-gray-200 bg-gray-50">
        <div className="flex items-center justify-between text-xs">
          <span className="text-gray-600">System Status</span>
          <div className="flex items-center space-x-1">
            <div className="w-2 h-2 bg-success-500 rounded-full"></div>
            <span className="text-success-600 font-medium">Operational</span>
          </div>
        </div>
        
        <div className="mt-2 flex items-center justify-between text-xs text-gray-500">
          <span>API Response</span>
          <span>{'<'} 200ms</span>
        </div>
        
        <div className="mt-1 flex items-center justify-between text-xs text-gray-500">
          <span>Memory Access</span>
          <span>{'<'} 100ms</span>
        </div>
      </div>

      {/* Settings */}
      <div className="p-4 border-t border-gray-200">
        <NavLink
          to="/settings"
          className={({ isActive }) =>
            `flex items-center space-x-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              isActive
                ? 'bg-gray-100 text-gray-900'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
            }`
          }
        >
          <Settings className="w-4 h-4" />
          <span>Settings</span>
        </NavLink>
      </div>
    </aside>
  )
}

export default Sidebar