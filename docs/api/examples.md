# DRYAD.AI API Examples

**Version:** 1.0  
**Last Updated:** 2025-10-13

---

## Table of Contents

1. [Python Examples](#python-examples)
2. [JavaScript Examples](#javascript-examples)
3. [cURL Examples](#curl-examples)
4. [Common Workflows](#common-workflows)

---

## Python Examples

### Basic Setup

```python
import requests
from typing import Dict, Any

class DryadClient:
    def __init__(self, api_key: str, base_url: str = "https://api.dryad.ai/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        })
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make API request."""
        url = f"{self.base_url}{endpoint}"
        response = self.session.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()
    
    def get(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        return self._request("GET", endpoint, **kwargs)
    
    def post(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        return self._request("POST", endpoint, **kwargs)
    
    def put(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        return self._request("PUT", endpoint, **kwargs)
    
    def delete(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        return self._request("DELETE", endpoint, **kwargs)
```

### List Agents

```python
client = DryadClient(api_key="dryad_sk_...")

# List all agents
agents = client.get("/agents")
print(f"Found {len(agents['agents'])} agents")

# Filter by capability
code_agents = client.get("/agents", params={"capability": "code_analysis"})
```

### Execute Workflow

```python
# Start a workflow
workflow = client.post("/workflows", json={
    "task": "Analyze this codebase for security vulnerabilities",
    "context": {
        "repository": "https://github.com/user/repo",
        "branch": "main"
    },
    "options": {
        "max_iterations": 5,
        "timeout_seconds": 300
    }
})

workflow_id = workflow["workflow_id"]
print(f"Workflow started: {workflow_id}")

# Poll for completion
import time

while True:
    status = client.get(f"/workflows/{workflow_id}")
    
    if status["status"] == "completed":
        print("Workflow completed!")
        print(status["result"])
        break
    elif status["status"] == "failed":
        print("Workflow failed!")
        print(status.get("error"))
        break
    
    print(f"Status: {status['status']}")
    time.sleep(5)
```

### Store and Retrieve Memory

```python
# Store memory
memory = client.post("/memory", json={
    "content": "The user prefers Python over JavaScript",
    "metadata": {
        "category": "preferences",
        "source": "conversation"
    },
    "memory_type": "long_term"
})

memory_id = memory["memory_id"]
print(f"Memory stored: {memory_id}")

# Retrieve memory
retrieved = client.get(f"/memory/{memory_id}")
print(f"Content: {retrieved['content']}")

# Search memory
results = client.post("/memory/search", json={
    "query": "What programming language does the user prefer?",
    "limit": 5
})

for result in results["results"]:
    print(f"Score: {result['score']:.2f} - {result['content']}")
```

### Execute Code

```python
# Execute Python code
result = client.post("/execute", json={
    "language": "python",
    "code": """
import math
print(f"Pi is approximately {math.pi:.2f}")
    """,
    "timeout": 30
})

print(f"Output: {result['stdout']}")
print(f"Execution time: {result['execution_time_ms']}ms")
```

---

## JavaScript Examples

### Basic Setup

```javascript
class DryadClient {
  constructor(apiKey, baseUrl = 'https://api.dryad.ai/v1') {
    this.apiKey = apiKey;
    this.baseUrl = baseUrl;
  }

  async request(method, endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const response = await fetch(url, {
      method,
      headers: {
        'X-API-Key': this.apiKey,
        'Content-Type': 'application/json',
        ...options.headers
      },
      ...options
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  get(endpoint, params = {}) {
    const queryString = new URLSearchParams(params).toString();
    const url = queryString ? `${endpoint}?${queryString}` : endpoint;
    return this.request('GET', url);
  }

  post(endpoint, data) {
    return this.request('POST', endpoint, {
      body: JSON.stringify(data)
    });
  }

  put(endpoint, data) {
    return this.request('PUT', endpoint, {
      body: JSON.stringify(data)
    });
  }

  delete(endpoint) {
    return this.request('DELETE', endpoint);
  }
}
```

### List Agents

```javascript
const client = new DryadClient('dryad_sk_...');

// List all agents
const agents = await client.get('/agents');
console.log(`Found ${agents.agents.length} agents`);

// Filter by capability
const codeAgents = await client.get('/agents', {
  capability: 'code_analysis'
});
```

### Execute Workflow

```javascript
// Start workflow
const workflow = await client.post('/workflows', {
  task: 'Analyze this codebase for security vulnerabilities',
  context: {
    repository: 'https://github.com/user/repo',
    branch: 'main'
  },
  options: {
    max_iterations: 5,
    timeout_seconds: 300
  }
});

console.log(`Workflow started: ${workflow.workflow_id}`);

// Poll for completion
async function waitForWorkflow(workflowId) {
  while (true) {
    const status = await client.get(`/workflows/${workflowId}`);
    
    if (status.status === 'completed') {
      console.log('Workflow completed!');
      return status.result;
    } else if (status.status === 'failed') {
      throw new Error(`Workflow failed: ${status.error}`);
    }
    
    console.log(`Status: ${status.status}`);
    await new Promise(resolve => setTimeout(resolve, 5000));
  }
}

const result = await waitForWorkflow(workflow.workflow_id);
console.log(result);
```

---

## cURL Examples

### List Agents

```bash
curl -X GET "https://api.dryad.ai/v1/agents" \
  -H "X-API-Key: dryad_sk_..."
```

### Execute Workflow

```bash
curl -X POST "https://api.dryad.ai/v1/workflows" \
  -H "X-API-Key: dryad_sk_..." \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Analyze this codebase",
    "context": {
      "repository": "https://github.com/user/repo"
    }
  }'
```

### Store Memory

```bash
curl -X POST "https://api.dryad.ai/v1/memory" \
  -H "X-API-Key: dryad_sk_..." \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Important information",
    "metadata": {
      "category": "notes"
    }
  }'
```

### Search Memory

```bash
curl -X POST "https://api.dryad.ai/v1/memory/search" \
  -H "X-API-Key: dryad_sk_..." \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What did we discuss?",
    "limit": 10
  }'
```

---

## Common Workflows

### 1. Code Analysis Workflow

```python
def analyze_code(client, repository_url):
    """Analyze code quality and security."""
    
    # Start workflow
    workflow = client.post("/workflows", json={
        "task": "Analyze code quality and security",
        "context": {"repository": repository_url},
        "agents": ["code_analyzer", "security_scanner"]
    })
    
    # Wait for completion
    workflow_id = workflow["workflow_id"]
    while True:
        status = client.get(f"/workflows/{workflow_id}")
        if status["status"] in ["completed", "failed"]:
            break
        time.sleep(5)
    
    # Store results in memory
    if status["status"] == "completed":
        client.post("/memory", json={
            "content": f"Code analysis for {repository_url}",
            "metadata": {
                "type": "analysis_result",
                "repository": repository_url,
                "result": status["result"]
            }
        })
    
    return status["result"]
```

### 2. Conversational Agent

```python
def chat_with_agent(client, message, conversation_id=None):
    """Have a conversation with an agent."""
    
    # Search for relevant context
    context = client.post("/memory/search", json={
        "query": message,
        "filters": {"conversation_id": conversation_id} if conversation_id else {},
        "limit": 5
    })
    
    # Execute workflow with context
    workflow = client.post("/workflows", json={
        "task": message,
        "context": {
            "conversation_history": context["results"],
            "conversation_id": conversation_id
        }
    })
    
    # Wait for response
    workflow_id = workflow["workflow_id"]
    while True:
        status = client.get(f"/workflows/{workflow_id}")
        if status["status"] == "completed":
            response = status["result"]["response"]
            break
        time.sleep(1)
    
    # Store conversation in memory
    client.post("/memory", json={
        "content": f"User: {message}\nAgent: {response}",
        "metadata": {
            "type": "conversation",
            "conversation_id": conversation_id or workflow_id
        }
    })
    
    return response
```

### 3. Batch Processing

```python
def process_batch(client, items):
    """Process multiple items in parallel."""
    
    workflows = []
    
    # Start all workflows
    for item in items:
        workflow = client.post("/workflows", json={
            "task": f"Process {item}",
            "context": {"item": item}
        })
        workflows.append(workflow["workflow_id"])
    
    # Wait for all to complete
    results = []
    while workflows:
        for workflow_id in workflows[:]:
            status = client.get(f"/workflows/{workflow_id}")
            if status["status"] == "completed":
                results.append(status["result"])
                workflows.remove(workflow_id)
            elif status["status"] == "failed":
                workflows.remove(workflow_id)
        
        if workflows:
            time.sleep(2)
    
    return results
```

---

**Last Updated:** 2025-10-13

