'use client';

import React from 'react';
import { Layout } from '@/components/layout/Layout';
import { Button } from '@/components/ui/Button';
import { 
  Upload, 
  FileText, 
  MessageSquare, 
  BarChart3, 
  Clock, 
  Star,
  TrendingUp,
  Users,
  Database,
  Zap
} from 'lucide-react';
import { useAuth } from '@/lib/auth/context';
import { formatRelativeTime } from '@/utils/helpers';

export default function DashboardPage() {
  const { user } = useAuth();

  // Mock data - replace with real data from API
  const stats = {
    totalDocuments: 24,
    totalQueries: 156,
    storageUsed: 2.4, // GB
    storageLimit: 10, // GB
    recentActivity: [
      {
        id: '1',
        type: 'upload',
        description: 'Uploaded "Project Proposal.pdf"',
        timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
      },
      {
        id: '2',
        type: 'query',
        description: 'Asked about budget allocation',
        timestamp: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
      },
      {
        id: '3',
        type: 'upload',
        description: 'Uploaded "Meeting Notes.docx"',
        timestamp: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
      },
    ],
    popularTags: [
      { tag: 'research', count: 12, trend: 'up' as const },
      { tag: 'meeting-notes', count: 8, trend: 'stable' as const },
      { tag: 'proposals', count: 6, trend: 'up' as const },
      { tag: 'reports', count: 4, trend: 'down' as const },
    ],
  };

  const quickActions = [
    {
      title: 'Upload Documents',
      description: 'Add new documents to your library',
      icon: Upload,
      href: '/upload',
      color: 'bg-blue-500',
    },
    {
      title: 'Start Chat',
      description: 'Ask questions about your documents',
      icon: MessageSquare,
      href: '/chat',
      color: 'bg-green-500',
    },
    {
      title: 'Browse Documents',
      description: 'View and organize your files',
      icon: FileText,
      href: '/documents',
      color: 'bg-purple-500',
    },
    {
      title: 'View Analytics',
      description: 'See usage statistics and insights',
      icon: BarChart3,
      href: '/analytics',
      color: 'bg-orange-500',
    },
  ];

  return (
    <Layout>
      <div className="space-y-8">
        {/* Welcome Section */}
        <div className="bg-white rounded-lg shadow-soft p-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                Welcome back, {user?.name?.split(' ')[0] || 'there'}!
              </h1>
              <p className="text-gray-600 mt-1">
                Here's what's happening with your documents and AI assistant.
              </p>
            </div>
            <div className="hidden sm:block">
              <div className="flex items-center space-x-2 text-sm text-gray-500">
                <Clock className="w-4 h-4" />
                <span>Last active: {formatRelativeTime(user?.lastLogin || new Date().toISOString())}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            title="Documents"
            value={stats.totalDocuments}
            icon={FileText}
            color="text-blue-600"
            bgColor="bg-blue-100"
          />
          <StatCard
            title="AI Queries"
            value={stats.totalQueries}
            icon={MessageSquare}
            color="text-green-600"
            bgColor="bg-green-100"
          />
          <StatCard
            title="Storage Used"
            value={`${stats.storageUsed}GB`}
            subtitle={`of ${stats.storageLimit}GB`}
            icon={Database}
            color="text-purple-600"
            bgColor="bg-purple-100"
          />
          <StatCard
            title="Processing"
            value="Fast"
            subtitle="< 2s avg"
            icon={Zap}
            color="text-orange-600"
            bgColor="bg-orange-100"
          />
        </div>

        {/* Quick Actions */}
        <div className="bg-white rounded-lg shadow-soft p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {quickActions.map((action) => (
              <QuickActionCard key={action.title} {...action} />
            ))}
          </div>
        </div>

        {/* Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Recent Activity */}
          <div className="lg:col-span-2 bg-white rounded-lg shadow-soft p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Recent Activity</h2>
              <Button variant="outline" size="sm">
                View All
              </Button>
            </div>
            <div className="space-y-4">
              {stats.recentActivity.map((activity) => (
                <ActivityItem key={activity.id} activity={activity} />
              ))}
            </div>
          </div>

          {/* Popular Tags */}
          <div className="bg-white rounded-lg shadow-soft p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Popular Tags</h2>
            <div className="space-y-3">
              {stats.popularTags.map((tag) => (
                <TagItem key={tag.tag} tag={tag} />
              ))}
            </div>
          </div>
        </div>

        {/* Storage Usage */}
        <div className="bg-white rounded-lg shadow-soft p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Storage Usage</h2>
            <span className="text-sm text-gray-500">
              {stats.storageUsed}GB of {stats.storageLimit}GB used
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-primary-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${(stats.storageUsed / stats.storageLimit) * 100}%` }}
            />
          </div>
          <div className="flex justify-between text-xs text-gray-500 mt-2">
            <span>0GB</span>
            <span>{stats.storageLimit}GB</span>
          </div>
        </div>
      </div>
    </Layout>
  );
}

// Stat Card Component
interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  bgColor: string;
}

function StatCard({ title, value, subtitle, icon: Icon, color, bgColor }: StatCardProps) {
  return (
    <div className="bg-white rounded-lg shadow-soft p-6">
      <div className="flex items-center">
        <div className={`p-2 rounded-lg ${bgColor}`}>
          <Icon className={`w-6 h-6 ${color}`} />
        </div>
        <div className="ml-4">
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <div className="flex items-baseline">
            <p className="text-2xl font-semibold text-gray-900">{value}</p>
            {subtitle && (
              <p className="ml-2 text-sm text-gray-500">{subtitle}</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// Quick Action Card Component
interface QuickActionCardProps {
  title: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  href: string;
  color: string;
}

function QuickActionCard({ title, description, icon: Icon, href, color }: QuickActionCardProps) {
  return (
    <a
      href={href}
      className="block p-4 border border-gray-200 rounded-lg hover:border-gray-300 hover:shadow-md transition-all duration-200"
    >
      <div className="flex items-center mb-2">
        <div className={`p-2 rounded-lg ${color}`}>
          <Icon className="w-5 h-5 text-white" />
        </div>
        <h3 className="ml-3 font-medium text-gray-900">{title}</h3>
      </div>
      <p className="text-sm text-gray-600">{description}</p>
    </a>
  );
}

// Activity Item Component
interface ActivityItemProps {
  activity: {
    id: string;
    type: string;
    description: string;
    timestamp: string;
  };
}

function ActivityItem({ activity }: ActivityItemProps) {
  const getIcon = () => {
    switch (activity.type) {
      case 'upload':
        return <Upload className="w-4 h-4 text-blue-500" />;
      case 'query':
        return <MessageSquare className="w-4 h-4 text-green-500" />;
      default:
        return <FileText className="w-4 h-4 text-gray-500" />;
    }
  };

  return (
    <div className="flex items-center space-x-3">
      <div className="flex-shrink-0">
        {getIcon()}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm text-gray-900">{activity.description}</p>
        <p className="text-xs text-gray-500">{formatRelativeTime(activity.timestamp)}</p>
      </div>
    </div>
  );
}

// Tag Item Component
interface TagItemProps {
  tag: {
    tag: string;
    count: number;
    trend: 'up' | 'down' | 'stable';
  };
}

function TagItem({ tag }: TagItemProps) {
  const getTrendIcon = () => {
    switch (tag.trend) {
      case 'up':
        return <TrendingUp className="w-3 h-3 text-green-500" />;
      case 'down':
        return <TrendingUp className="w-3 h-3 text-red-500 rotate-180" />;
      default:
        return null;
    }
  };

  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center space-x-2">
        <span className="text-sm font-medium text-gray-900">#{tag.tag}</span>
        {getTrendIcon()}
      </div>
      <span className="text-sm text-gray-500">{tag.count}</span>
    </div>
  );
}
