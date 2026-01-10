# Tool Creation System Design (MCP-Style)

**Version**: 1.0.0  
**Status**: Design Phase  
**Purpose**: Easy tool creation, installation, and marketplace

---

## System Overview

The Tool Creation System enables users to:
- Create custom tools using templates
- Package tools as MCP servers
- Install tools into agents
- Share tools via marketplace
- Manage tool versions and dependencies

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│     Tool Creation System (Level 6)                  │
│  ┌──────────────────────────────────────────────┐  │
│  │ Tool Creation Wizard                         │  │
│  │ - Template selection                         │  │
│  │ - Code generation                            │  │
│  │ - Configuration                              │  │
│  │ - Testing                                    │  │
│  └──────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────┐  │
│  │ MCP Server Packager                          │  │
│  │ - Package tool as MCP server                 │  │
│  │ - Generate Docker container                  │  │
│  │ - Create installation script                 │  │
│  └──────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────┐  │
│  │ Tool Marketplace                             │  │
│  │ - Browse tools                               │  │
│  │ - Install tools                              │  │
│  │ - Rate & review                              │  │
│  │ - Manage versions                            │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ DRYAD Tool Registry (Level 0)                       │
│ - Tool registration                                 │
│ - Tool discovery                                    │
│ - Tool versioning                                   │
└─────────────────────────────────────────────────────┘
```

---

## Tool Creation Wizard

### Step 1: Select Template

```yaml
Templates:
  - "API Integration"
    description: "Call external APIs"
    language: "python"
    
  - "Data Processing"
    description: "Process and transform data"
    language: "python"
    
  - "Calculation"
    description: "Mathematical operations"
    language: "python"
    
  - "Search & Retrieval"
    description: "Search and retrieve information"
    language: "python"
    
  - "File Operations"
    description: "Read/write files"
    language: "python"
    
  - "Custom"
    description: "Start from scratch"
    language: "python"
```

### Step 2: Define Tool Properties

```python
class ToolDefinition:
    # Metadata
    name: str
    version: str
    description: str
    author: str
    
    # Functionality
    input_schema: Dict[str, Any]  # JSON Schema
    output_schema: Dict[str, Any]
    
    # Configuration
    parameters: Dict[str, ParameterDefinition]
    environment_variables: List[str]
    
    # Capabilities
    capabilities: List[str]
    dependencies: List[str]
    
    # Constraints
    rate_limit: Optional[int]
    timeout_seconds: int
    max_retries: int
    
    # Metadata
    tags: List[str]
    category: str
    difficulty: str  # "easy", "medium", "hard"
```

### Step 3: Implement Tool Logic

**Template Example: API Integration**

```python
# tool_template.py
from typing import Any, Dict
import httpx

class APITool:
    """
    Template for creating API integration tools.
    Replace the implementation with your API logic.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.api_key = config.get("api_key")
        self.base_url = config.get("base_url")
        self.timeout = config.get("timeout", 30)
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the tool with given parameters.
        
        Args:
            **kwargs: Tool-specific parameters
        
        Returns:
            Dict with results
        """
        # TODO: Implement your API call logic
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/endpoint",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=self.timeout,
                params=kwargs
            )
            return response.json()
    
    def validate_input(self, **kwargs) -> bool:
        """Validate input parameters"""
        # TODO: Add validation logic
        return True
```

### Step 4: Configure & Test

```python
# tool_config.yaml
name: "Weather API Tool"
version: "1.0.0"
description: "Get weather information from OpenWeather API"

input_schema:
  type: "object"
  properties:
    city:
      type: "string"
      description: "City name"
    units:
      type: "string"
      enum: ["metric", "imperial"]
      default: "metric"

output_schema:
  type: "object"
  properties:
    temperature:
      type: "number"
    description:
      type: "string"
    humidity:
      type: "number"

parameters:
  api_key:
    type: "string"
    required: true
    description: "OpenWeather API key"

environment_variables:
  - "OPENWEATHER_API_KEY"

capabilities:
  - "weather_retrieval"
  - "location_based_search"

dependencies:
  - "httpx>=0.24.0"

tags:
  - "weather"
  - "api"
  - "external-service"

category: "data-retrieval"
difficulty: "easy"
```

---

## MCP Server Packaging

### Automatic Docker Generation

```dockerfile
# Generated Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy tool code
COPY tool_code/ /app/

# Install dependencies
RUN pip install -r requirements.txt

# Install MCP server
RUN pip install mcp

# Expose MCP port
EXPOSE 8000

# Start MCP server
CMD ["python", "-m", "mcp.server", "--tool", "tool_template.py"]
```

### Installation Script

```bash
#!/bin/bash
# install_tool.sh

TOOL_NAME="weather-api-tool"
TOOL_VERSION="1.0.0"

echo "Installing $TOOL_NAME v$TOOL_VERSION..."

# Pull Docker image
docker pull registry.example.com/$TOOL_NAME:$TOOL_VERSION

# Register with DRYAD Tool Registry
curl -X POST http://localhost:8000/api/v1/tools/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "'$TOOL_NAME'",
    "version": "'$TOOL_VERSION'",
    "docker_image": "registry.example.com/'$TOOL_NAME':'$TOOL_VERSION'",
    "mcp_port": 8000
  }'

echo "Installation complete!"
```

---

## Tool Marketplace

### Marketplace API

```
GET    /api/v1/marketplace/tools              # List tools
GET    /api/v1/marketplace/tools/{id}         # Get tool details
POST   /api/v1/marketplace/tools              # Submit tool
PATCH  /api/v1/marketplace/tools/{id}         # Update tool
DELETE /api/v1/marketplace/tools/{id}         # Remove tool
GET    /api/v1/marketplace/tools/search       # Search tools
POST   /api/v1/marketplace/tools/{id}/install # Install tool
GET    /api/v1/marketplace/tools/{id}/reviews # Get reviews
POST   /api/v1/marketplace/tools/{id}/review  # Submit review
```

### Tool Submission Template

```yaml
# tool_submission.yaml
metadata:
  name: "Weather API Tool"
  version: "1.0.0"
  author: "John Doe"
  license: "MIT"
  
description: |
  Get real-time weather information for any location.
  Supports multiple units and detailed forecasts.

documentation:
  readme: "README.md"
  examples: "examples/"
  api_docs: "docs/api.md"

installation:
  method: "docker"
  docker_image: "registry.example.com/weather-api-tool:1.0.0"
  
testing:
  unit_tests: "tests/unit/"
  integration_tests: "tests/integration/"
  test_coverage: 0.85

security:
  requires_api_key: true
  api_key_env_var: "OPENWEATHER_API_KEY"
  permissions: ["read_weather_data"]

performance:
  average_latency_ms: 150
  max_concurrent_calls: 100
  rate_limit: "1000 calls/hour"

ratings:
  average_rating: 4.5
  total_reviews: 42
  download_count: 1250
```

---

## Integration with Agent Creation

### Tool Selection in Agent Designer

```python
# During agent creation
agent_config = {
    "name": "Weather Expert",
    "tools": [
        {
            "tool_id": "weather-api-tool",
            "version": "1.0.0",
            "config": {
                "api_key": "${OPENWEATHER_API_KEY}",
                "units": "metric"
            }
        },
        {
            "tool_id": "location-search-tool",
            "version": "2.1.0",
            "config": {}
        }
    ]
}
```

---

## Tool Versioning & Dependency Management

```python
class ToolVersion:
    tool_id: str
    version: str
    created_at: datetime
    
    # Compatibility
    compatible_with: List[str]  # Agent versions
    breaking_changes: List[str]
    
    # Dependencies
    dependencies: Dict[str, str]  # tool_id -> version
    
    # Status
    status: str  # "beta", "stable", "deprecated"
    deprecation_date: Optional[datetime]
```

---

## Tool Validation Framework

### Pre-Submission Checks
- [ ] Code quality (linting, type checking)
- [ ] Security scan (no hardcoded secrets)
- [ ] Performance baseline
- [ ] Documentation completeness
- [ ] Test coverage > 80%

### Post-Installation Checks
- [ ] Tool initialization
- [ ] Configuration validation
- [ ] Capability verification
- [ ] Performance testing

---

## API Endpoints

```
# Tool Management
POST   /api/v1/tools/create              # Create tool
GET    /api/v1/tools/{id}                # Get tool
PATCH  /api/v1/tools/{id}                # Update tool
DELETE /api/v1/tools/{id}                # Delete tool

# Tool Installation
POST   /api/v1/agents/{id}/tools/install # Install tool in agent
GET    /api/v1/agents/{id}/tools         # List agent tools
DELETE /api/v1/agents/{id}/tools/{tool}  # Remove tool from agent

# Marketplace
GET    /api/v1/marketplace/tools         # Browse marketplace
POST   /api/v1/marketplace/tools/submit  # Submit tool
GET    /api/v1/marketplace/tools/search  # Search tools
```

---

## Implementation Phases

**Phase 1**: Tool creation wizard and templates  
**Phase 2**: MCP server packaging  
**Phase 3**: Tool marketplace  
**Phase 4**: Installation automation  
**Phase 5**: Tool versioning and dependency management  

**Status**: Ready for implementation

