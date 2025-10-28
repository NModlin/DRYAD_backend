# Dashboard Architecture Design

**Version**: 1.0.0  
**Status**: Design Phase  
**Purpose**: Multi-platform dashboard for Agentic University System

---

## System Overview

Three-tier dashboard architecture:
1. **Local Desktop Dashboard** - Immediate use, no cloud required
2. **Web Dashboard** - Future cloud deployment
3. **GCP Free Tier Option** - Lightweight cloud hosting

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│         User Interface Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │
│  │ Desktop App  │  │ Web Browser  │  │ Mobile   │ │
│  │ (Electron)   │  │ (React)      │  │ (Future) │ │
│  └──────────────┘  └──────────────┘  └──────────┘ │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│         API Gateway & WebSocket Layer               │
│  - Authentication                                   │
│  - Real-time updates                                │
│  - Message routing                                  │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│         Backend Services (Phases 1-6)               │
│  - University Manager                               │
│  - Curriculum Engine                                │
│  - Arena Framework                                  │
│  - Training Pipeline                                │
└─────────────────────────────────────────────────────┘
```

---

## 1. Local Desktop Dashboard (Electron)

### Technology Stack
- **Framework**: Electron + React
- **State Management**: Redux
- **Real-time**: WebSocket client
- **Styling**: Tailwind CSS
- **Charts**: Chart.js / D3.js

### Features

**Home Dashboard**
- Quick stats (agents, competitions, progress)
- Recent activity feed
- Quick actions (create agent, start competition)
- System health status

**Agent Management**
- Create/edit agents
- View agent details
- Character design interface
- Tool management
- Performance analytics

**Curriculum Tracking**
- Enrolled curricula
- Progress visualization
- Competency assessment
- Recommended next steps

**Arena Viewer**
- Live competition streaming
- Leaderboards
- Historical results
- Agent matchups

**Settings**
- API configuration
- Preferences
- Data management
- About & help

### Installation

```bash
# Download and install
npm install
npm run build
npm run electron

# Or use pre-built installer
# Download from releases page
```

### Local Backend Connection

```javascript
// config.js
const API_CONFIG = {
  local: {
    api_url: "http://localhost:8000",
    ws_url: "ws://localhost:8000/ws",
    mode: "local"
  }
};
```

---

## 2. Web Dashboard (React + FastAPI)

### Technology Stack
- **Frontend**: React 18 + TypeScript
- **Backend**: FastAPI (existing)
- **Hosting**: GCP Cloud Run (free tier)
- **Database**: PostgreSQL (existing)
- **Real-time**: WebSocket

### Features (Same as Desktop)
- Agent management
- Curriculum tracking
- Arena viewer
- Analytics dashboard
- User management

### Responsive Design
- Desktop: Full features
- Tablet: Optimized layout
- Mobile: Essential features only

---

## 3. GCP Free Tier Deployment

### GCP Services Used

```
┌─────────────────────────────────────────────────────┐
│         GCP Free Tier Services                      │
│  ┌──────────────────────────────────────────────┐  │
│  │ Cloud Run (2M requests/month free)           │  │
│  │ - Host FastAPI backend                       │  │
│  │ - Host React frontend                        │  │
│  └──────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────┐  │
│  │ Cloud SQL (1 shared core, 10GB storage)      │  │
│  │ - PostgreSQL database                        │  │
│  └──────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────┐  │
│  │ Cloud Storage (5GB free)                     │  │
│  │ - Agent artifacts                            │  │
│  │ - Training data                              │  │
│  └──────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────┐  │
│  │ Cloud Firestore (1GB storage, 50K reads)     │  │
│  │ - Real-time updates (optional)               │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

### GCP Setup Instructions

**Step 1: Create GCP Project**
```bash
gcloud projects create agentic-university
gcloud config set project agentic-university
```

**Step 2: Enable Services**
```bash
gcloud services enable run.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable storage.googleapis.com
```

**Step 3: Create Cloud SQL Instance**
```bash
gcloud sql instances create agentic-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1
```

**Step 4: Deploy Backend to Cloud Run**
```bash
# Build Docker image
docker build -t gcr.io/agentic-university/backend .

# Push to GCP
docker push gcr.io/agentic-university/backend

# Deploy
gcloud run deploy backend \
  --image gcr.io/agentic-university/backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

**Step 5: Deploy Frontend to Cloud Run**
```bash
# Build React app
npm run build

# Create Dockerfile for frontend
# Deploy
gcloud run deploy frontend \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

---

## 4. G.A.D System Integration (Governance & Decision)

### G.A.D Architecture

```
┌─────────────────────────────────────────────────────┐
│     G.A.D System (Governance & Decision)            │
│  ┌──────────────────────────────────────────────┐  │
│  │ Decision Queue                               │  │
│  │ - Pending decisions                          │  │
│  │ - Priority scoring                           │  │
│  │ - Timeout handling                           │  │
│  └──────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────┐  │
│  │ HITL Workflow                                │  │
│  │ - Human review interface                     │  │
│  │ - Approval/rejection                         │  │
│  │ - Feedback collection                        │  │
│  └──────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────┐  │
│  │ Policy Engine                                │  │
│  │ - Policy definitions                         │  │
│  │ - Policy enforcement                         │  │
│  │ - Audit logging                              │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

### Decision Types

```python
class Decision:
    decision_id: str
    type: str  # "agent_creation", "competition_start", "resource_allocation"
    status: str  # "pending", "approved", "rejected"
    
    # Context
    context: Dict[str, Any]
    created_at: datetime
    
    # HITL
    assigned_to: Optional[str]  # User ID
    reviewed_at: Optional[datetime]
    reviewed_by: Optional[str]
    
    # Outcome
    approved: Optional[bool]
    feedback: Optional[str]
    
    # Audit
    audit_log: List[AuditEntry]
```

### HITL Dashboard

**Decision Queue View**
- Pending decisions
- Priority indicators
- Context information
- Approve/Reject buttons
- Feedback form

**Policy Management**
- View active policies
- Create new policies
- Edit policies
- Policy history

**Audit Log**
- All decisions made
- Who made them
- When they were made
- Feedback provided

---

## 5. User Workflows

### Workflow 1: Create Agent
```
1. Click "Create Agent"
2. Select template or start blank
3. Configure properties
4. Design character
5. Select tools
6. Review & create
7. Agent appears in dashboard
```

### Workflow 2: Enroll in Curriculum
```
1. Select agent
2. Click "Enroll in Curriculum"
3. Choose curriculum
4. Confirm enrollment
5. View curriculum progress
```

### Workflow 3: Watch Competition
```
1. Go to Arena
2. Select competition
3. Click "Watch Live"
4. Real-time updates via WebSocket
5. View results
```

### Workflow 4: Create Tool
```
1. Click "Create Tool"
2. Select template
3. Implement logic
4. Configure parameters
5. Test tool
6. Submit to marketplace
```

---

## 6. Real-Time Features

### WebSocket Channels

```
/ws/dashboard/{user_id}
  - Agent updates
  - Competition results
  - Curriculum progress
  - System notifications

/ws/competition/{competition_id}
  - Live round updates
  - Score changes
  - Agent actions
  - Results

/ws/agent/{agent_id}
  - Status changes
  - Performance metrics
  - Tool execution
  - Error notifications
```

---

## 7. Implementation Phases

**Phase 1**: Local desktop dashboard (Electron)  
**Phase 2**: Web dashboard (React)  
**Phase 3**: GCP deployment setup  
**Phase 4**: G.A.D system integration  
**Phase 5**: Mobile responsiveness  

**Status**: Ready for implementation

