# Phase 2: UniAugment Integration Points

**Phase**: Specialization & Skill Trees  
**Component**: UniAugment Deployment System  
**Date**: October 23, 2025

---

## 📋 Overview

This document outlines all UniAugment components that need to be updated to support Phase 2 (Specialization & Skill Trees) features during deployment.

---

## 📁 Files to Modify

### 1. Configuration System

#### `UniAugment/config/stack_config.py`

**Add SpecializationConfig class** (after AgentCreationStudioConfig):

```python
class SpecializationConfig:
    """Specialization and Skill Tree configuration for Phase 2"""
    
    def __init__(self):
        pass
    
    @property
    def enabled(self) -> bool:
        """Check if Specialization system is enabled"""
        return os.getenv("SPECIALIZATION_SYSTEM_ENABLED", "false").lower() == "true"
    
    @property
    def skill_tree_enabled(self) -> bool:
        """Check if Skill Tree system is enabled"""
        return os.getenv("SKILL_TREE_SYSTEM_ENABLED", "false").lower() == "true"
    
    @property
    def default_specialization(self) -> str:
        """Get default specialization for new agents"""
        return os.getenv("DEFAULT_SPECIALIZATION", "data_science")
    
    @property
    def cross_specialization_enabled(self) -> bool:
        """Check if cross-specialization learning is enabled"""
        return os.getenv("ENABLE_CROSS_SPECIALIZATION", "true").lower() == "true"
    
    @property
    def cross_specialization_penalty(self) -> float:
        """Get cross-specialization learning penalty"""
        return float(os.getenv("CROSS_SPECIALIZATION_PENALTY", "0.2"))
    
    @property
    def available_specializations(self) -> list:
        """Get list of available specializations"""
        default_specs = [
            "memetics",
            "warfare_studies",
            "bioengineered_intelligence",
            "data_science",
            "philosophy",
            "engineering",
            "creative_arts",
            "custom"
        ]
        env_specs = os.getenv("AVAILABLE_SPECIALIZATIONS", "")
        if env_specs:
            return [s.strip() for s in env_specs.split(",")]
        return default_specs
    
    def get_config_summary(self) -> dict:
        """Get configuration summary"""
        return {
            "enabled": self.enabled,
            "skill_tree_enabled": self.skill_tree_enabled,
            "default_specialization": self.default_specialization,
            "cross_specialization_enabled": self.cross_specialization_enabled,
            "cross_specialization_penalty": self.cross_specialization_penalty,
            "available_specializations": self.available_specializations,
        }
```

**Update StackConfig.__init__()** to instantiate specialization:
```python
self.specialization = SpecializationConfig()
```

**Update get_stack_info()** to include specialization:
```python
"specialization": self.specialization.get_config_summary(),
```

---

### 2. Setup Scripts

#### `UniAugment/scripts/setup-arch-linux.sh`

**Add configure_specialization() function** (after configure_agent_studio):

```bash
configure_specialization() {
    print_header "Specialization & Skill Tree Configuration"
    
    # Ask if user wants to enable Specialization system
    read -p "Enable Specialization system? (y/n) [default: y]: " ENABLE_SPEC
    ENABLE_SPEC=${ENABLE_SPEC:-y}
    
    if [[ "$ENABLE_SPEC" =~ ^[Yy]$ ]]; then
        SPECIALIZATION_SYSTEM_ENABLED="true"
        print_success "Specialization system enabled"
        
        # Skill tree system
        read -p "Enable Skill Tree system? (y/n) [default: y]: " ENABLE_SKILLS
        ENABLE_SKILLS=${ENABLE_SKILLS:-y}
        if [[ "$ENABLE_SKILLS" =~ ^[Yy]$ ]]; then
            SKILL_TREE_SYSTEM_ENABLED="true"
            print_success "Skill Tree system enabled"
        else
            SKILL_TREE_SYSTEM_ENABLED="false"
        fi
        
        # Default specialization
        echo ""
        print_info "Available specializations:"
        echo "  1) Memetics"
        echo "  2) Warfare Studies"
        echo "  3) Bioengineered Intelligence"
        echo "  4) Data Science (default)"
        echo "  5) Philosophy"
        echo "  6) Engineering"
        echo "  7) Creative Arts"
        echo "  8) Custom"
        read -p "Select default specialization [4]: " SPEC_CHOICE
        SPEC_CHOICE=${SPEC_CHOICE:-4}
        
        case $SPEC_CHOICE in
            1) DEFAULT_SPECIALIZATION="memetics" ;;
            2) DEFAULT_SPECIALIZATION="warfare_studies" ;;
            3) DEFAULT_SPECIALIZATION="bioengineered_intelligence" ;;
            4) DEFAULT_SPECIALIZATION="data_science" ;;
            5) DEFAULT_SPECIALIZATION="philosophy" ;;
            6) DEFAULT_SPECIALIZATION="engineering" ;;
            7) DEFAULT_SPECIALIZATION="creative_arts" ;;
            8) DEFAULT_SPECIALIZATION="custom" ;;
            *) DEFAULT_SPECIALIZATION="data_science" ;;
        esac
        print_success "Default specialization: $DEFAULT_SPECIALIZATION"
        
        # Cross-specialization learning
        read -p "Enable cross-specialization learning? (y/n) [default: y]: " ENABLE_CROSS
        ENABLE_CROSS=${ENABLE_CROSS:-y}
        if [[ "$ENABLE_CROSS" =~ ^[Yy]$ ]]; then
            ENABLE_CROSS_SPECIALIZATION="true"
            CROSS_SPECIALIZATION_PENALTY="0.2"
        else
            ENABLE_CROSS_SPECIALIZATION="false"
            CROSS_SPECIALIZATION_PENALTY="0.0"
        fi
    else
        SPECIALIZATION_SYSTEM_ENABLED="false"
        SKILL_TREE_SYSTEM_ENABLED="false"
        ENABLE_CROSS_SPECIALIZATION="false"
        DEFAULT_SPECIALIZATION="data_science"
        CROSS_SPECIALIZATION_PENALTY="0.0"
        print_info "Specialization system disabled"
    fi
}
```

**Add to environment file generation** (in create_config_files function):

```bash
# Specialization & Skill Trees - Phase 2
SPECIALIZATION_SYSTEM_ENABLED=${SPECIALIZATION_SYSTEM_ENABLED:-false}
SKILL_TREE_SYSTEM_ENABLED=${SKILL_TREE_SYSTEM_ENABLED:-false}
DEFAULT_SPECIALIZATION=${DEFAULT_SPECIALIZATION:-data_science}
ENABLE_CROSS_SPECIALIZATION=${ENABLE_CROSS_SPECIALIZATION:-true}
CROSS_SPECIALIZATION_PENALTY=${CROSS_SPECIALIZATION_PENALTY:-0.2}
AVAILABLE_SPECIALIZATIONS=memetics,warfare_studies,bioengineered_intelligence,data_science,philosophy,engineering,creative_arts,custom
```

**Call configure_specialization() in main()**:
```bash
configure_agent_studio
configure_specialization  # Add this line
create_config_files
```

---

#### `UniAugment/scripts/setup-windows.ps1`

**Add Configure-Specialization function** (after Configure-Agent-Studio):

```powershell
function Configure-Specialization {
    Write-Header "Specialization & Skill Tree Configuration"
    
    # Ask if user wants to enable Specialization system
    $EnableSpec = Read-Host "Enable Specialization system? (y/n) [default: y]"
    if ([string]::IsNullOrWhiteSpace($EnableSpec)) { $EnableSpec = "y" }
    
    if ($EnableSpec -match "^[Yy]$") {
        $script:SPECIALIZATION_SYSTEM_ENABLED = "true"
        Write-Success "Specialization system enabled"
        
        # Skill tree system
        $EnableSkills = Read-Host "Enable Skill Tree system? (y/n) [default: y]"
        if ([string]::IsNullOrWhiteSpace($EnableSkills)) { $EnableSkills = "y" }
        if ($EnableSkills -match "^[Yy]$") {
            $script:SKILL_TREE_SYSTEM_ENABLED = "true"
            Write-Success "Skill Tree system enabled"
        } else {
            $script:SKILL_TREE_SYSTEM_ENABLED = "false"
        }
        
        # Default specialization
        Write-Host ""
        Write-Info "Available specializations:"
        Write-Host "  1) Memetics"
        Write-Host "  2) Warfare Studies"
        Write-Host "  3) Bioengineered Intelligence"
        Write-Host "  4) Data Science (default)"
        Write-Host "  5) Philosophy"
        Write-Host "  6) Engineering"
        Write-Host "  7) Creative Arts"
        Write-Host "  8) Custom"
        $SpecChoice = Read-Host "Select default specialization [4]"
        if ([string]::IsNullOrWhiteSpace($SpecChoice)) { $SpecChoice = "4" }
        
        switch ($SpecChoice) {
            "1" { $script:DEFAULT_SPECIALIZATION = "memetics" }
            "2" { $script:DEFAULT_SPECIALIZATION = "warfare_studies" }
            "3" { $script:DEFAULT_SPECIALIZATION = "bioengineered_intelligence" }
            "4" { $script:DEFAULT_SPECIALIZATION = "data_science" }
            "5" { $script:DEFAULT_SPECIALIZATION = "philosophy" }
            "6" { $script:DEFAULT_SPECIALIZATION = "engineering" }
            "7" { $script:DEFAULT_SPECIALIZATION = "creative_arts" }
            "8" { $script:DEFAULT_SPECIALIZATION = "custom" }
            default { $script:DEFAULT_SPECIALIZATION = "data_science" }
        }
        Write-Success "Default specialization: $($script:DEFAULT_SPECIALIZATION)"
        
        # Cross-specialization learning
        $EnableCross = Read-Host "Enable cross-specialization learning? (y/n) [default: y]"
        if ([string]::IsNullOrWhiteSpace($EnableCross)) { $EnableCross = "y" }
        if ($EnableCross -match "^[Yy]$") {
            $script:ENABLE_CROSS_SPECIALIZATION = "true"
            $script:CROSS_SPECIALIZATION_PENALTY = "0.2"
        } else {
            $script:ENABLE_CROSS_SPECIALIZATION = "false"
            $script:CROSS_SPECIALIZATION_PENALTY = "0.0"
        }
    } else {
        $script:SPECIALIZATION_SYSTEM_ENABLED = "false"
        $script:SKILL_TREE_SYSTEM_ENABLED = "false"
        $script:ENABLE_CROSS_SPECIALIZATION = "false"
        $script:DEFAULT_SPECIALIZATION = "data_science"
        $script:CROSS_SPECIALIZATION_PENALTY = "0.0"
        Write-Info "Specialization system disabled"
    }
}
```

**Add to environment file generation**:

```powershell
# Specialization & Skill Trees - Phase 2
SPECIALIZATION_SYSTEM_ENABLED=$($script:SPECIALIZATION_SYSTEM_ENABLED ?? 'false')
SKILL_TREE_SYSTEM_ENABLED=$($script:SKILL_TREE_SYSTEM_ENABLED ?? 'false')
DEFAULT_SPECIALIZATION=$($script:DEFAULT_SPECIALIZATION ?? 'data_science')
ENABLE_CROSS_SPECIALIZATION=$($script:ENABLE_CROSS_SPECIALIZATION ?? 'true')
CROSS_SPECIALIZATION_PENALTY=$($script:CROSS_SPECIALIZATION_PENALTY ?? '0.2')
AVAILABLE_SPECIALIZATIONS=memetics,warfare_studies,bioengineered_intelligence,data_science,philosophy,engineering,creative_arts,custom
```

---

#### `UniAugment/scripts/deploy-full-stack.sh`

**Add to collect_inputs() function**:

```bash
echo -e "\n${YELLOW}=== Specialization & Skill Tree Configuration ===${NC}"
read -p "Enable Specialization system? (y/n) [y]: " ENABLE_SPEC
ENABLE_SPEC=${ENABLE_SPEC:-y}

if [[ "$ENABLE_SPEC" =~ ^[Yy]$ ]]; then
    SPECIALIZATION_SYSTEM_ENABLED="true"
    log_success "Specialization system enabled"
    
    read -p "Enable Skill Tree system? (y/n) [y]: " ENABLE_SKILLS
    ENABLE_SKILLS=${ENABLE_SKILLS:-y}
    if [[ "$ENABLE_SKILLS" =~ ^[Yy]$ ]]; then
        SKILL_TREE_SYSTEM_ENABLED="true"
    else
        SKILL_TREE_SYSTEM_ENABLED="false"
    fi
    
    read -p "Default specialization (data_science): " DEFAULT_SPEC
    DEFAULT_SPECIALIZATION=${DEFAULT_SPEC:-data_science}
    
    log_success "Specialization configuration complete"
else
    SPECIALIZATION_SYSTEM_ENABLED="false"
    SKILL_TREE_SYSTEM_ENABLED="false"
    DEFAULT_SPECIALIZATION="data_science"
    log "Specialization system disabled"
fi
```

**Add to create_env_file() function**:

```bash
# Specialization & Skill Trees - Phase 2
SPECIALIZATION_SYSTEM_ENABLED=${SPECIALIZATION_SYSTEM_ENABLED:-false}
SKILL_TREE_SYSTEM_ENABLED=${SKILL_TREE_SYSTEM_ENABLED:-false}
DEFAULT_SPECIALIZATION=${DEFAULT_SPECIALIZATION:-data_science}
ENABLE_CROSS_SPECIALIZATION=true
CROSS_SPECIALIZATION_PENALTY=0.2
AVAILABLE_SPECIALIZATIONS=memetics,warfare_studies,bioengineered_intelligence,data_science,philosophy,engineering,creative_arts,custom
```

---

### 3. Docker Compose Files

Update all 4 compose files with Phase 2 environment variables:

#### `UniAugment/compose/docker-compose.full.yml`
#### `UniAugment/compose/docker-compose.hybrid.yml`
#### `UniAugment/compose/docker-compose.lite.yml`
#### `UniAugment/compose/docker-compose.arch-api.yml`

**Add to environment section** (after Phase 1 variables):

```yaml
# Specialization & Skill Trees - Phase 2
- SPECIALIZATION_SYSTEM_ENABLED=${SPECIALIZATION_SYSTEM_ENABLED:-false}
- SKILL_TREE_SYSTEM_ENABLED=${SKILL_TREE_SYSTEM_ENABLED:-false}
- DEFAULT_SPECIALIZATION=${DEFAULT_SPECIALIZATION:-data_science}
- ENABLE_CROSS_SPECIALIZATION=${ENABLE_CROSS_SPECIALIZATION:-true}
- CROSS_SPECIALIZATION_PENALTY=${CROSS_SPECIALIZATION_PENALTY:-0.2}
- AVAILABLE_SPECIALIZATIONS=${AVAILABLE_SPECIALIZATIONS:-memetics,warfare_studies,bioengineered_intelligence,data_science,philosophy,engineering,creative_arts,custom}
```

---

### 4. Documentation

#### `UniAugment/DISTRIBUTED_SETUP_GUIDE.md`

**Add Phase 2 section** (after Phase 1 section):

```markdown
## 🎓 Specialization & Skill Trees (Phase 2)

### What is the Specialization System?

The Specialization System allows agents to focus on specific domains with custom skill trees and progression paths. Phase 2 includes:

**Specialization Types:**
- Memetics (cultural evolution, meme analysis)
- Warfare Studies (strategy, game theory)
- Bioengineered Intelligence (neural networks, hybrid systems)
- Data Science (analytics, ML, predictive modeling)
- Philosophy (ethics, reasoning, knowledge systems)
- Engineering (systems design, optimization)
- Creative Arts (generative art, music, narrative)
- Custom (user-defined)

**Skill Tree System:**
- Custom skill nodes with prerequisites
- Experience-based progression
- Capability bonuses and personality shifts
- Tool and competition unlocks

### Enabling Specialization System

During setup, you'll be prompted:

```
Enable Specialization system? (y/n) [default: y]: y
Enable Skill Tree system? (y/n) [default: y]: y
Select default specialization [4]: 4
Enable cross-specialization learning? (y/n) [default: y]: y
```

### Configuration

Specialization settings are stored in `.env.distributed`:

```bash
# Specialization & Skill Trees - Phase 2
SPECIALIZATION_SYSTEM_ENABLED=true
SKILL_TREE_SYSTEM_ENABLED=true
DEFAULT_SPECIALIZATION=data_science
ENABLE_CROSS_SPECIALIZATION=true
CROSS_SPECIALIZATION_PENALTY=0.2
AVAILABLE_SPECIALIZATIONS=memetics,warfare_studies,bioengineered_intelligence,data_science,philosophy,engineering,creative_arts,custom
```
```

---

## 📊 Summary

**Files to Modify**: 9 files
- 1 configuration file
- 3 setup scripts
- 4 Docker Compose files
- 1 documentation file

**Environment Variables Added**: 6 variables
- `SPECIALIZATION_SYSTEM_ENABLED`
- `SKILL_TREE_SYSTEM_ENABLED`
- `DEFAULT_SPECIALIZATION`
- `ENABLE_CROSS_SPECIALIZATION`
- `CROSS_SPECIALIZATION_PENALTY`
- `AVAILABLE_SPECIALIZATIONS`

---

**Status**: Ready for implementation  
**Next**: Begin UniAugment integration after DRYAD_backend Phase 2 is complete

