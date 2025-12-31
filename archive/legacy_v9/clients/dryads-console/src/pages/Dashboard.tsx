import React from 'react'
import { Link } from 'react-router-dom'
import { 
  TreePine, 
  Brain, 
  BookOpen, 
  FileText, 
  Folder, 
  Users,
  Zap,
  TrendingUp,
  Clock
} from 'lucide-react'
import { useAuth } from '../hooks/useAuth'

const Dashboard: React.FC = () => {
  const { user } = useAuth()

  const quickStats = [
    { label: 'Active Groves', value: '12', icon: TreePine, color: 'text-blue-600', change: '+2' },
    { label: 'Memory Records', value: '1,247', icon: BookOpen, color: 'text-green-600', change: '+15' },
    { label: 'Oracle Consultations', value: '89', icon: Brain, color: 'text-purple-600', change: '+7' },
    { label: 'Files Managed', value: '156', icon: Folder, color: 'text-orange-600', change: '+3' },
  ]

  const recentActivity = [
    { action: 'Created new grove', grove: 'Research Project', time: '2 hours ago', user: user?.name },
    { action: 'Oracle consultation', grove: 'Technical Analysis', time: '4 hours ago', user: 'Memory Keeper' },
    { action: 'File uploaded', grove: 'Documentation', time: '1 day ago', user: user?.name },
    { action: 'Branch suggestion', grove: 'Exploration', time: '2 days ago', user: 'AI Assistant' },
  ]

  return (
    <div className="space-y-8">
      {/* Welcome Section */}
      <div className="bg-white rounded-lg shadow-soft p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              Welcome back, {user?.name?.split(' ')[0] || 'there'}!
            </h1>
            <p className="text-gray-600 mt-1">
              Your quantum knowledge tree is ready for exploration.
            </p>
          </div>
          <div className="flex items-center space-x-2 text-sm text-gray-500">
            <Zap className="w-4 h-4 text-green-500" />
            <span>System: Operational</span>
          </div>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {quickStats.map((stat) => (
          <div key={stat.label} className="bg-white rounded-lg shadow-soft p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">{stat.label}</p>
                <div className="flex items-baseline space-x-2 mt-1">
                  <p className="text-2xl font-semibold text-gray-900">{stat.value}</p>
                  <span className="text-sm text-green-600 flex items-center">
                    <TrendingUp className="w-3 h-3 mr-1" />
                    {stat.change}
                  </span>
                </div>
              </div>
              <div className={`p-3 rounded-lg bg-gray-100`}>
                <stat.icon className={`w-6 h-6 ${stat.color}`} />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Activity */}
        <div className="bg-white rounded-lg shadow-soft p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h2>
          <div className="space-y-4">
            {recentActivity.map((activity, index) => (
              <div key={index} className="flex items-center space-x-3">
                <div className="flex-shrink-0 w-2 h-2 bg-primary-500 rounded-full"></div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-900">
                    <span className="font-medium">{activity.user}</span> {activity.action}
                  </p>
                  <p className="text-xs text-gray-500">{activity.grove}</p>
                </div>
                <div className="flex items-center space-x-1 text-xs text-gray-500">
                  <Clock className="w-3 h-3" />
                  <span>{activity.time}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Quick Links */}
        <div className="bg-white rounded-lg shadow-soft p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Access</h2>
          <div className="grid grid-cols-2 gap-4">
            <Link
              to="/groves"
              className="flex flex-col items-center p-4 border border-gray-200 rounded-lg hover:border-primary-300 hover:bg-primary-50 transition-colors"
            >
              <TreePine className="w-8 h-8 text-primary-600 mb-2" />
              <span className="text-sm font-medium text-gray-900">Grove Explorer</span>
            </Link>
            
            <Link
              to="/oracle"
              className="flex flex-col items-center p-4 border border-gray-200 rounded-lg hover:border-purple-300 hover:bg-purple-50 transition-colors"
            >
              <Brain className="w-8 h-8 text-purple-600 mb-2" />
              <span className="text-sm font-medium text-gray-900">Oracle</span>
            </Link>
            
            <Link
              to="/memory"
              className="flex flex-col items-center p-4 border border-gray-200 rounded-lg hover:border-green-300 hover:bg-green-50 transition-colors"
            >
              <BookOpen className="w-8 h-8 text-green-600 mb-2" />
              <span className="text-sm font-medium text-gray-900">Memory Keeper</span>
            </Link>
            
            <Link
              to="/files"
              className="flex flex-col items-center p-4 border border-gray-200 rounded-lg hover:border-orange-300 hover:bg-orange-50 transition-colors"
            >
              <Folder className="w-8 h-8 text-orange-600 mb-2" />
              <span className="text-sm font-medium text-gray-900">File Manager</span>
            </Link>
          </div>
        </div>
      </div>

      {/* System Status */}
      <div className="bg-white rounded-lg shadow-soft p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">System Performance</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center">
            <div className="text-2xl font-bold text-primary-600">{'<'} 200ms</div>
            <p className="text-sm text-gray-600">API Response Time</p>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">99.9%</div>
            <p className="text-sm text-gray-600">Uptime</p>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">32/32</div>
            <p className="text-sm text-gray-600">Endpoints Active</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Dashboard