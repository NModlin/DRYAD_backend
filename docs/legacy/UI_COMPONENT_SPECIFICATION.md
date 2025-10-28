# 🎓 DRYAD University System - UI Component Specification

**Version**: 1.0.0  
**Status**: Specification Complete - Ready for Development  
**Date**: October 23, 2025  
**Target**: React component library with TypeScript and API integration

---

## 📋 Component Architecture Overview

### **Component Hierarchy**
```
App
├── AuthenticationProvider
├── UniversityProvider
├── Layout
│   ├── Header
│   ├── Navigation
│   └── MainContent
├── Dashboard (Role-based)
│   ├── StudentDashboard
│   ├── FacultyDashboard
│   └── AdminDashboard
└── Modals & Overlays
    ├── AgentCreationWizard
    ├── CompetitionSetup
    └── CurriculumManager
```

### **State Management Structure**
```typescript
interface AppState {
  auth: AuthState;
  university: UniversityState;
  agents: AgentState;
  curriculum: CurriculumState;
  competitions: CompetitionState;
  ui: UIState;
}
```

---

## 🔐 Authentication & Layout Components

### **1. AuthenticationProvider**
**Purpose**: Manage user authentication and role-based access

```typescript
interface AuthState {
  user: User | null;
  token: string | null;
  role: 'student' | 'faculty' | 'admin';
  isLoading: boolean;
}

// API Integration
- POST /auth/login
- POST /auth/refresh
- GET /auth/profile
```

### **2. Layout Component**
**Purpose**: Main application layout with responsive navigation

```tsx
const Layout: React.FC<{ children: ReactNode }> = ({ children }) => (
  <div className="min-h-screen bg-gray-50">
    <Header />
    <Navigation />
    <main className="p-6">{children}</main>
  </div>
);
```

### **3. Header Component**
**Purpose**: Display user info, notifications, and quick actions

```tsx
const Header: React.FC = () => (
  <header className="bg-white shadow-sm border-b">
    <div className="max-w-7xl mx-auto px-4 py-3">
      <div className="flex justify-between items-center">
        <UniversityLogo />
        <UserProfile />
        <NotificationBell />
        <QuickActions />
      </div>
    </div>
  </header>
);
```

### **4. Navigation Component**
**Purpose**: Role-based navigation menu

```tsx
const Navigation: React.FC = () => {
  const { role } = useAuth();
  
  return (
    <nav className="bg-white shadow-sm">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex space-x-8">
          <NavLink to="/dashboard" label="Dashboard" />
          {role === 'student' && <StudentNavLinks />}
          {role === 'faculty' && <FacultyNavLinks />}
          {role === 'admin' && <AdminNavLinks />}
        </div>
      </div>
    </nav>
  );
};
```

---

## 🎓 Student Dashboard Components

### **5. StudentDashboard**
**Purpose**: Main student dashboard with overview panels

```tsx
const StudentDashboard: React.FC = () => {
  const { agentId, universityId } = useStudentContext();
  
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <QuickStatsPanel agentId={agentId} />
      <CurrentProgressPanel agentId={agentId} />
      <RecentActivityPanel agentId={agentId} />
      <SkillTreeVisualization agentId={agentId} />
      <UpcomingCompetitions universityId={universityId} />
      <LeaderboardPanel universityId={universityId} />
      <ResourceUsagePanel agentId={agentId} />
    </div>
  );
};
```

### **6. QuickStatsPanel**
**Purpose**: Display key agent statistics

```tsx
const QuickStatsPanel: React.FC<{ agentId: string }> = ({ agentId }) => {
  const { data: stats, isLoading } = useAgentStats(agentId);
  
  if (isLoading) return <LoadingSkeleton />;
  
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">Quick Stats</h3>
      <div className="space-y-3">
        <StatItem label="Competency Score" value={stats.competencyScore} format="percent" />
        <StatItem label="Training Hours" value={stats.trainingHours} format="hours" />
        <StatItem label="Challenges Completed" value={stats.challengesCompleted} />
        <StatItem label="Current Level" value={stats.currentLevel} />
      </div>
    </div>
  );
};

// API Integration
- GET /universities/{id}/agents/{id}/progress
```

### **7. SkillTreeVisualization**
**Purpose**: Interactive skill tree display

```tsx
const SkillTreeVisualization: React.FC<{ agentId: string }> = ({ agentId }) => {
  const { data: skillTree, isLoading } = useSkillTree(agentId);
  const { data: progress } = useSkillProgress(agentId);
  
  return (
    <div className="bg-white rounded-lg shadow p-6 col-span-2">
      <h3 className="text-lg font-semibold mb-4">Skill Tree</h3>
      <SkillTreeGraph 
        tree={skillTree} 
        progress={progress}
        onNodeClick={(node) => setSelectedNode(node)}
      />
      {selectedNode && <SkillNodeDetails node={selectedNode} />}
    </div>
  );
};

// API Integration
- GET /skill-trees/{tree_id}
- GET /agents/{id}/skills/progress
```

### **8. RealTimeCompetitionFeed**
**Purpose**: Live competition updates via WebSocket

```tsx
const RealTimeCompetitionFeed: React.FC<{ universityId: string }> = ({ universityId }) => {
  const [competitions, setCompetitions] = useState<Competition[]>([]);
  
  useEffect(() => {
    const ws = new WebSocket(`wss://api.dryad.ai/ws/university/${universityId}`);
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'competition_update') {
        setCompetitions(prev => updateCompetitions(prev, data));
      }
    };
    
    return () => ws.close();
  }, [universityId]);
  
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">Live Competitions</h3>
      <div className="space-y-3">
        {competitions.map(comp => (
          <CompetitionCard key={comp.id} competition={comp} />
        ))}
      </div>
    </div>
  );
};
```

---

## 🎓 Faculty Dashboard Components

### **9. FacultyDashboard**
**Purpose**: University management interface for faculty

```tsx
const FacultyDashboard: React.FC = () => {
  const { universityId } = useFacultyContext();
  
  return (
    <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
      <UniversityStatsPanel universityId={universityId} />
      <AgentPerformancePanel universityId={universityId} />
      <CompetitionActivityPanel universityId={universityId} />
      <PerformanceAnalytics universityId={universityId} />
      <ResourceAllocationPanel universityId={universityId} />
      <RecentActivityPanel universityId={universityId} />
    </div>
  );
};
```

### **10. CurriculumManager**
**Purpose**: Create and manage curriculum paths

```tsx
const CurriculumManager: React.FC<{ universityId: string }> = ({ universityId }) => {
  const [curricula, setCurricula] = useState<Curriculum[]>([]);
  
  const handleCreateCurriculum = async (data: CurriculumCreate) => {
    const result = await api.createCurriculum(universityId, data);
    setCurricula(prev => [...prev, result]);
  };
  
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-semibold">Curriculum Management</h3>
        <Button onClick={() => setShowCreateModal(true)}>
          Create New Curriculum
        </Button>
      </div>
      
      <CurriculumList curricula={curricula} />
      
      {showCreateModal && (
        <CurriculumCreationModal
          onSubmit={handleCreateCurriculum}
          onClose={() => setShowCreateModal(false)}
        />
      )}
    </div>
  );
};

// API Integration
- GET /universities/{id}/curriculum/paths
- POST /universities/{id}/curriculum/paths
- PUT /universities/{id}/curriculum/paths/{id}
```

### **11. CompetitionSetupWizard**
**Purpose**: Multi-step competition creation

```tsx
const CompetitionSetupWizard: React.FC<{ universityId: string }> = ({ universityId }) => {
  const [step, setStep] = useState(1);
  const [competitionData, setCompetitionData] = useState<Partial<Competition>>({});
  
  const steps = [
    { title: 'Basic Info', component: BasicInfoStep },
    { title: 'Schedule', component: ScheduleStep },
    { title: 'Evaluation', component: EvaluationStep },
    { title: 'Participants', component: ParticipantsStep },
    { title: 'Review', component: ReviewStep },
  ];
  
  const CurrentStep = steps[step - 1].component;
  
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <WizardProgress steps={steps} currentStep={step} />
      <CurrentStep
        data={competitionData}
        onChange={setCompetitionData}
        onNext={() => setStep(step + 1)}
        onBack={() => setStep(step - 1)}
      />
    </div>
  );
};

// API Integration
- POST /universities/{id}/competitions
```

### **12. PerformanceAnalytics**
**Purpose**: Advanced analytics visualization

```tsx
const PerformanceAnalytics: React.FC<{ universityId: string }> = ({ universityId }) => {
  const { data: analytics, isLoading } = useUniversityAnalytics(universityId);
  
  return (
    <div className="bg-white rounded-lg shadow p-6 col-span-2">
      <h3 className="text-lg font-semibold mb-4">Performance Analytics</h3>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <AnalyticsChart 
          type="radar" 
          data={analytics.competencyDistribution}
          title="Competency Distribution"
        />
        <AnalyticsChart
          type="line"
          data={analytics.progressTrends}
          title="Progress Trends"
        />
        <AnalyticsChart
          type="bar"
          data={analytics.skillGaps}
          title="Skill Gaps"
        />
      </div>
    </div>
  );
};
```

---

## ⚙️ Administrator Dashboard Components

### **13. AdminDashboard**
**Purpose**: System-wide administration interface

```tsx
const AdminDashboard: React.FC = () => {
  return (
    <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
      <SystemHealthPanel />
      <UniversityOverview />
      <UserActivityPanel />
      <MultiUniversityAnalytics />
      <ResourceManagement />
      <RecentAlertsPanel />
    </div>
  );
};
```

### **14. SystemHealthPanel**
**Purpose**: Monitor system health and performance

```tsx
const SystemHealthPanel: React.FC = () => {
  const { data: health, isLoading } = useSystemHealth();
  
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">System Health</h3>
      <div className="space-y-4">
        <HealthStatus 
          service="API Server" 
          status={health.api} 
          metrics={health.apiMetrics}
        />
        <HealthStatus 
          service="Database" 
          status={health.database} 
          metrics={health.dbMetrics}
        />
        <HealthStatus 
          service="WebSocket" 
          status={health.websocket} 
          metrics={health.wsMetrics}
        />
      </div>
    </div>
  );
};
```

### **15. UniversityManagement**
**Purpose**: Create and manage university instances

```tsx
const UniversityManagement: React.FC = () => {
  const { data: universities, mutate } = useUniversities();
  
  const handleCreateUniversity = async (data: UniversityCreate) => {
    const newUni = await api.createUniversity(data);
    mutate([...universities, newUni]);
  };
  
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-semibold">University Management</h3>
        <UniversityCreationWizard onSubmit={handleCreateUniversity} />
      </div>
      
      <UniversityList universities={universities} />
    </div>
  );
};

// API Integration
- GET /universities
- POST /universities
- PUT /universities/{id}
- DELETE /universities/{id}
```

### **16. UserManagement**
**Purpose**: Manage users and permissions

```tsx
const UserManagement: React.FC = () => {
  const { data: users, isLoading } = useUsers();
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">User Management</h3>
      
      <UserTable 
        users={users} 
        onEdit={setSelectedUser}
        onRoleChange={handleRoleChange}
      />
      
      {selectedUser && (
        <UserEditModal
          user={selectedUser}
          onSave={handleUserUpdate}
          onClose={() => setSelectedUser(null)}
        />
      )}
    </div>
  );
};
```

---

## 🎨 Shared Components & Utilities

### **17. Data Visualization Components**

#### **ProgressBar**
```tsx
interface ProgressBarProps {
  value: number;
  max?: number;
  label?: string;
  format?: 'percent' | 'fraction';
}

const ProgressBar: React.FC<ProgressBarProps> = ({ 
  value, 
  max = 100, 
  label,
  format = 'percent'
}) => {
  const percentage = (value / max) * 100;
  
  return (
    <div className="w-full">
      {label && <span className="text-sm text-gray-600">{label}</span>}
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div 
          className="bg-blue-600 h-2 rounded-full transition-all"
          style={{ width: `${percentage}%` }}
        />
      </div>
      <span className="text-xs text-gray-500">
        {format === 'percent' ? `${percentage}%` : `${value}/${max}`}
      </span>
    </div>
  );
};
```

#### **RadarChart**
```tsx
const RadarChart: React.FC<RadarChartProps> = ({ data, dimensions }) => {
  return (
    <div className="relative">
      <svg viewBox="0 0 100 100" className="w-full h-64">
        {/* Draw radar chart using D3.js or custom SVG */}
        {data.map((point, index) => (
          <RadarPoint key={index} point={point} dimensions={dimensions} />
        ))}
      </svg>
    </div>
  );
};
```

### **18. Form Components**

#### **FormField**
```tsx
interface FormFieldProps {
  label: string;
  error?: string;
  children: ReactNode;
}

const FormField: React.FC<FormFieldProps> = ({ label, error, children }) => (
  <div className="mb-4">
    <label className="block text-sm font-medium text-gray-700 mb-1">
      {label}
    </label>
    {children}
    {error && <p className="text-red-500 text-xs mt-1">{error}</p>}
  </div>
);
```

#### **SelectInput**
```tsx
interface SelectInputProps {
  value: string;
  onChange: (value: string) => void;
  options: Array<{ value: string; label: string }>;
  placeholder?: string;
}

const SelectInput: React.FC<SelectInputProps> = ({
  value,
  onChange,
  options,
  placeholder
}) => (
  <select
    value={value}
    onChange={(e) => onChange(e.target.value)}
    className="w-full px-3 py-2 border border-gray-300 rounded-md"
  >
    {placeholder && <option value="">{placeholder}</option>}
    {options.map(option => (
      <option key={option.value} value={option.value}>
        {option.label}
      </option>
    ))}
  </select>
);
```

### **19. API Integration Hooks**

#### **useAgentStats**
```tsx
const useAgentStats = (agentId: string) => {
  return useQuery({
    queryKey: ['agent-stats', agentId],
    queryFn: () => api.getAgentStats(agentId),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};
```

#### **useUniversityCompetitions**
```tsx
const useUniversityCompetitions = (universityId: string, filters = {}) => {
  return useQuery({
    queryKey: ['competitions', universityId, filters],
    queryFn: () => api.getCompetitions(universityId, filters),
  });
};
```

#### **useWebSocket**
```tsx
const useWebSocket = (topic: string, callback: (data: any) => void) => {
  useEffect(() => {
    const ws = new WebSocket(`wss://api.dryad.ai/ws/${topic}`);
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      callback(data);
    };
    
    return () => ws.close();
  }, [topic, callback]);
};
```

---

## 🔧 Development Guidelines

### **Component Structure**
```typescript
// 1. Define Props Interface
interface ComponentProps {
  requiredProp: string;
  optionalProp?: number;
  onClick?: () => void;
}

// 2. Create Component with Default Export
const MyComponent: React.FC<ComponentProps> = ({ 
  requiredProp, 
  optionalProp = 0,
  onClick 
}) => {
  // 3. Use hooks at top level
  const [state, setState] = useState();
  
  // 4. Event handlers
  const handleClick = () => {
    onClick?.();
  };
  
  // 5. Return JSX
  return (
    <div onClick={handleClick}>
      {requiredProp} - {optionalProp}
    </div>
  );
};

export default MyComponent;
```

### **Error Handling**
```tsx
const ErrorBoundary: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [hasError, setHasError] = useState(false);
  
  useEffect(() => {
    const handleError = () => setHasError(true);
    window.addEventListener('error', handleError);
    return () => window.removeEventListener('error', handleError);
  }, []);
  
  if (hasError) {
    return <ErrorFallback />;
  }
  
  return children;
};
```

### **Performance Optimization**
```tsx
// Use React.memo for expensive components
const ExpensiveComponent = React.memo(({ data }) => {
  return <div>{/* expensive rendering */}</div>;
});

// Use useCallback for event handlers
const handleClick = useCallback(() => {
  // handler logic
}, [dependencies]);

// Use useMemo for expensive calculations
const computedValue = useMemo(() => {
  return expensiveCalculation(data);
}, [data]);
```

---

## 📊 Testing Strategy

### **Unit Tests**
```typescript
// Component test example
describe('QuickStatsPanel', () => {
  it('displays agent statistics correctly', () => {
    render(<QuickStatsPanel agentId="test-agent" />);
    
    expect(screen.getByText('Competency Score')).toBeInTheDocument();
    expect(screen.getByText('72%')).toBeInTheDocument();
  });
});
```

### **Integration Tests**
```typescript
describe('StudentDashboard', () => {
  it('loads and displays all panels', async () => {
    render(<StudentDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('Quick Stats')).toBeInTheDocument();
      expect(screen.getByText('Skill Tree')).toBeInTheDocument();
    });
  });
});
```

### **E2E Tests**
```typescript
describe('Agent Creation Flow', () => {
  it('completes agent creation successfully', () => {
    // Test complete user journey
  });
});
```

---

## 🚀 Deployment Checklist

### **Pre-Deployment**
- [ ] All components pass TypeScript compilation
- [ ] Unit test coverage >90%
- [ ] Accessibility audit completed
- [ ] Performance benchmarks met
- [ ] Cross-browser testing completed

### **Post-Deployment**
- [ ] Monitor error rates and performance
- [ ] Gather user feedback
- [ ] Plan iterative improvements
- [ ] Update documentation

---

## ✅ Conclusion

This component specification provides a complete blueprint for implementing the DRYAD University System UI. The design leverages the production-ready backend APIs while maintaining scalability, accessibility, and performance.

**Status**: ✅ **Specification Complete - Ready for Development**