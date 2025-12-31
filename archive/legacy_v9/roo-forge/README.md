# DRYAD Grove IDE: GAD-Style Multi-Agent Development System

A Governed Agentic Development (GAD) system built on the DRYAD.AI ecosystem, featuring hierarchical agent orchestration, university-based training, and integrated IDE capabilities.

**Formerly known as ROO-Forge, now evolved into the DRYAD Grove IDE**

## 🌟 Project Overview

DRYAD Grove IDE implements a 4-layer hierarchical agentic development system using:
- **GAD Modes** for agent orchestration
- **DRYAD.AI Ecosystem** for backend infrastructure
- **University Training System** for agent education
- **Integrated IDE Environment** for comprehensive development
- **Tool Registry** for dynamic capabilities

## 🏗️ Architecture

```
roo-forge/
├── README.md
├── .roomodes              # Enhanced Roo Code modes with GAD integration
├── .roo/
│   └── mcp.json          # MCP server configuration for DRYAD services
├── configs/
│   ├── gad_modes.yaml    # GAD layer definitions
│   └── integration.yaml  # DRYAD integration settings
├── modes/
│   ├── orchestrator/     # Layer 3: Forest Keeper (Planning)
│   ├── reviewer/         # Layer 2: Guardian (Quality Review)
│   ├── executor/         # Layer 1: Branch Weaver (Code Execution)
│   └── human/           # Layer 4: Human Provost (Oversight)
├── templates/
│   └── agent_sheets/     # GAD-specific agent templates
└── tests/
    └── gad_integration/  # Integration tests
```

## 🚀 Quick Start

1. **Install DRYAD.AI Backend** (if not already installed)
2. **Copy .roomodes** to your project root
3. **Configure MCP servers** in .roo/mcp.json
4. **Start DRYAD Grove IDE** with integrated development environment

## 📋 GAD Layers

| Layer | DRYAD Component | Role | Roo Code Mode |
|-------|----------------|------|---------------|
| 4: HITL | University Admin + Tool Registry | Human Provost | human-provost |
| 3: Planning | Agent Orchestrator + Knowledge Trees | Forest Keeper | forest-keeper |
| 2: Review | Tool Registry Service + Security | Guardian | guardian-reviewer |
| 1: Execution | Agent Factory + Custom Agents | Branch Weaver | branch-weaver |

## 🔗 Integration Points

- **University System**: Agent training and curriculum management
- **Agent Creation Studio**: Custom GAD agent development
- **Tool Registry**: Dynamic tool access and validation
- **Knowledge Trees**: Project context and learning persistence
- **Multi-tenant Architecture**: Client isolation and scaling

## 📚 Documentation

- [GAD Implementation Guide](docs/gad_implementation.md)
- [University Training Curriculum](docs/university_curriculum.md)
- [Agent Studio Templates](docs/agent_templates.md)
- [Deployment Guide](docs/deployment.md)

## 🎯 Current Phase

**Phase 1**: Roo Code Mode Integration with DRYAD Ecosystem
- [x] Project structure creation
- [ ] Enhanced .roomodes configuration
- [ ] MCP server integration
- [ ] DRYAD service connectors

## 🤝 Contributing

This project builds upon the DRYAD.AI ecosystem. See main DRYAD documentation for contribution guidelines.

## 📄 License

MIT License - See DRYAD.AI license for details.