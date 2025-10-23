# 🤖 Self-Healing System - Complete Setup Guide

## Overview

The DRYAD.AI Self-Healing System implements **Governed Agentic Development (GAD)** - an autonomous code repair system with mandatory human oversight. The system detects errors in logs, generates fixes using AI agents, and applies them only after human approval.

---

## 🏗️ Architecture

### Components

1. **Guardian Agent** (`app/core/guardian.py`)
   - Monitors `logs/gremlins_errors.log` in real-time
   - Detects and classifies errors
   - Deduplicates repeated errors
   - Submits to orchestrator

2. **Planning Agent** (Existing Multi-Agent System)
   - Analyzes error context
   - Generates structured fix plans
   - Creates test specifications

3. **Human Review** (Microsoft Teams Integration)
   - Sends Adaptive Cards to Teams
   - Requires explicit approval/rejection
   - **Critical safety gate** - no code changes without approval

4. **Execution Agent** (`app/workers/self_healing_worker.py`)
   - Applies approved code changes
   - Runs validation tests
   - Rolls back on failure

5. **Database** (`self_healing_tasks` table)
   - Tracks all tasks and their status
   - Stores plans, reviews, and execution logs
   - Provides audit trail

---

## 📋 Prerequisites

### 1. Database Migration

Run the migration to create the `self_healing_tasks` table:

```bash
# Run migration
alembic upgrade head
```

### 2. Microsoft Teams Setup

**Create Incoming Webhook:**

1. Open your Teams channel (e.g., #gremlins-monitoring)
2. Click "..." → "Connectors"
3. Search for "Incoming Webhook"
4. Click "Configure"
5. Name it "DRYAD.AI Self-Healing"
6. Copy the webhook URL
7. Save it to `.env`:

```bash
TEAMS_WEBHOOK_URL="https://outlook.office.com/webhook/..."
```

### 3. Public URL (for Callbacks)

**Option A: ngrok (Development)**

```bash
# Install ngrok
# Download from: https://ngrok.com/download

# Start backend
python start.py basic

# In new terminal, start ngrok
ngrok http 8000

# Copy the HTTPS URL (e.g., https://abc123.ngrok.io)
# Add to .env:
PUBLIC_CALLBACK_URL="https://abc123.ngrok.io"
```

**Option B: Production Domain**

```bash
# Use your actual domain
PUBLIC_CALLBACK_URL="https://api.yourdomain.com"
```

### 4. Enable Self-Healing

Update `.env`:

```bash
ENABLE_SELF_HEALING="true"
```

---

## 🚀 Quick Start

### 1. Start the Backend

```bash
python start.py basic
```

You should see:
```
🛡️ Starting Self-Healing System...
✅ Self-Healing System started
```

### 2. Verify Guardian is Running

```bash
curl http://localhost:8000/api/v1/orchestrator/self-healing/stats
```

Expected response:
```json
{
  "status_counts": {
    "pending_review": 0,
    "approved": 0,
    "rejected": 0,
    "executing": 0,
    "completed": 0,
    "failed": 0
  },
  "guardian": {
    "running": true,
    "errors_detected": 0,
    "errors_submitted": 0,
    "errors_deduplicated": 0
  }
}
```

### 3. Test with Simulated Error

Create a test error in the logs:

```bash
# Create test error
python scripts/test_self_healing.py inject-error
```

Or manually add to `logs/gremlins_errors.log`:

```json
{"timestamp": "2025-10-01T14:00:00", "level": "ERROR", "message": "KeyError: 'user_id'", "module": "api.v1.endpoints.chat", "line": 152}
```

### 4. Check Teams for Notification

Within a few seconds, you should receive an Adaptive Card in Teams with:
- Error details
- Proposed fix
- Approve/Reject buttons

### 5. Approve the Fix

Click "✅ Approve Fix" in Teams.

### 6. Monitor Execution

```bash
# Check task status
curl http://localhost:8000/api/v1/orchestrator/self-healing/tasks
```

---

## 🔧 Configuration

### Environment Variables

```bash
# Enable/disable self-healing
ENABLE_SELF_HEALING="true"

# Teams webhook for notifications
TEAMS_WEBHOOK_URL="https://outlook.office.com/webhook/..."

# Public URL for callbacks
PUBLIC_CALLBACK_URL="https://abc123.ngrok.io"

# Guardian settings (optional)
GUARDIAN_CHECK_INTERVAL="2.0"  # Seconds between log checks
GUARDIAN_DEDUP_WINDOW="300"    # Seconds to remember errors

# Worker settings (optional)
WORKER_CHECK_INTERVAL="10.0"   # Seconds between task checks
```

### Severity Filtering

The Guardian only processes errors with severity:
- **Critical**: Database errors, system failures
- **High**: KeyError, AttributeError, TypeError
- **Medium**: Other exceptions
- **Low**: Warnings (skipped)

---

## 📊 API Endpoints

### Create Self-Healing Task

```bash
POST /api/v1/orchestrator/self-healing
```

**Request:**
```json
{
  "task_type": "self_healing_fix",
  "error_details": {
    "error_type": "KeyError",
    "error_message": "user_id",
    "file_path": "app/api/v1/endpoints/chat.py",
    "line_number": 152,
    "stack_trace": "...",
    "severity": "high",
    "timestamp": "2025-10-01T14:00:00Z",
    "hash": "abc123"
  },
  "goal": "Fix KeyError by adding validation",
  "timestamp": "2025-10-01T14:00:00Z"
}
```

### Review Task

```bash
POST /api/v1/orchestrator/review/{task_id}
```

**Request:**
```json
{
  "decision": "approved",
  "reviewer": "user@company.com",
  "comments": "Looks good"
}
```

### Get Task Details

```bash
GET /api/v1/orchestrator/tasks/{task_id}
```

### List Tasks

```bash
GET /api/v1/orchestrator/self-healing/tasks?status=pending_review&limit=10
```

### Get Statistics

```bash
GET /api/v1/orchestrator/self-healing/stats
```

---

## 🧪 Testing

### Manual Testing

1. **Inject Test Error:**
   ```bash
   python scripts/test_self_healing.py inject-error
   ```

2. **Check Guardian Detected It:**
   ```bash
   curl http://localhost:8000/api/v1/orchestrator/self-healing/stats
   ```

3. **Verify Teams Notification:**
   - Check Teams channel for Adaptive Card

4. **Approve Fix:**
   - Click "✅ Approve Fix" in Teams

5. **Verify Execution:**
   ```bash
   curl http://localhost:8000/api/v1/orchestrator/self-healing/tasks
   ```

### Automated Testing

```bash
# Run self-healing tests
pytest tests/test_self_healing.py -v

# Test Guardian
pytest tests/test_guardian.py -v

# Test Teams integration
pytest tests/test_teams_notifier.py -v

# Test worker
pytest tests/test_self_healing_worker.py -v
```

---

## 🔍 Monitoring

### View Logs

```bash
# Guardian logs
tail -f logs/gremlins_app.log | grep Guardian

# Worker logs
tail -f logs/gremlins_app.log | grep "Self-Healing Worker"

# All self-healing activity
tail -f logs/gremlins_app.log | grep -E "(Guardian|Self-Healing)"
```

### Check Task Status

```bash
# All tasks
curl http://localhost:8000/api/v1/orchestrator/self-healing/tasks

# Pending review
curl http://localhost:8000/api/v1/orchestrator/self-healing/tasks?status=pending_review

# Completed
curl http://localhost:8000/api/v1/orchestrator/self-healing/tasks?status=completed

# Failed
curl http://localhost:8000/api/v1/orchestrator/self-healing/tasks?status=failed
```

### Statistics Dashboard

```bash
curl http://localhost:8000/api/v1/orchestrator/self-healing/stats | jq
```

---

## 🛡️ Safety Mechanisms

### 1. Human Approval Required
- **No code changes without explicit approval**
- Review via Teams Adaptive Cards
- Reviewer identity tracked

### 2. Test Validation
- All changes validated with tests
- Automatic rollback on test failure

### 3. Backup & Rollback
- Files backed up before modification
- Automatic restoration on failure

### 4. Audit Trail
- All actions logged in database
- Reviewer, timestamps, decisions tracked
- Execution logs preserved

### 5. Rate Limiting
- Deduplication prevents repeated fixes
- Configurable time windows

### 6. Severity Filtering
- Only high/critical errors processed
- Low severity errors ignored

---

## 🚨 Troubleshooting

### Guardian Not Starting

**Check logs:**
```bash
tail -f logs/gremlins_app.log | grep Guardian
```

**Verify enabled:**
```bash
grep ENABLE_SELF_HEALING .env
```

### Teams Notifications Not Received

**Test webhook:**
```bash
curl -X POST $TEAMS_WEBHOOK_URL \
  -H "Content-Type: application/json" \
  -d '{"text": "Test message"}'
```

**Check webhook URL:**
```bash
grep TEAMS_WEBHOOK_URL .env
```

### Callbacks Not Working

**Verify ngrok:**
```bash
curl https://abc123.ngrok.io/api/v1/health/status
```

**Check callback URL:**
```bash
grep PUBLIC_CALLBACK_URL .env
```

### Worker Not Executing

**Check worker status:**
```bash
curl http://localhost:8000/api/v1/orchestrator/self-healing/stats
```

**View worker logs:**
```bash
tail -f logs/gremlins_app.log | grep "Self-Healing Worker"
```

---

## 📈 Success Metrics

Track these metrics to measure effectiveness:

- **Detection Rate**: % of errors detected by Guardian
- **Fix Success Rate**: % of approved fixes that resolve errors
- **Review Time**: Average time from detection to approval
- **False Positive Rate**: % of fixes that cause new errors
- **System Uptime**: Improvement in uptime after self-healing

---

## 🔮 Future Enhancements

1. **ML-based Error Classification**
   - Train model to predict fix success
   - Auto-approve low-risk fixes

2. **Pattern Learning**
   - Learn from successful fixes
   - Improve future fix generation

3. **Multi-Platform Notifications**
   - Slack integration
   - Discord integration
   - Email notifications

4. **Advanced Code Analysis**
   - Static analysis before applying
   - Dependency impact analysis
   - Security vulnerability checks

5. **Proactive Monitoring**
   - Detect potential issues before errors
   - Performance degradation detection
   - Resource leak detection

---

## 📚 Documentation

- **Architecture**: See implementation spec in conversation
- **API Reference**: http://localhost:8000/docs
- **Database Schema**: `app/database/models/self_healing.py`
- **Guardian**: `app/core/guardian.py`
- **Worker**: `app/workers/self_healing_worker.py`
- **Teams Integration**: `app/integrations/teams_notifier.py`

---

**Your self-healing system is ready!** 🤖✨


