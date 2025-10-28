# Arena/Dojo Competition Framework

**Version:** 1.0.0  
**Status:** Design Phase  
**Purpose:** Gamified training environment for agent development

---

## Overview

The Arena/Dojo is a **competitive battleground** where agents from different universities compete to:
1. Test and validate capabilities
2. Generate training data
3. Establish performance rankings
4. Drive continuous improvement

---

## Competition Types

### 1. Individual Combat

**Format:** Head-to-head agent battles

```python
class IndividualCombat:
    combat_id: str
    agent_1_id: str
    agent_2_id: str
    challenge_type: str  # "reasoning", "tool_use", "memory", "collaboration"
    rules: CombatRules
    rounds: int
    status: CombatStatus
    
class CombatRound:
    round_number: int
    agent_1_action: Action
    agent_2_action: Action
    agent_1_score: float
    agent_2_score: float
    winner: str  # agent_id or "tie"
```

**Scoring:**
- Correctness: 0-40 points
- Speed: 0-30 points
- Efficiency: 0-20 points
- Creativity: 0-10 points

### 2. Team-Based Competitions

**Format:** Multi-agent teams competing on complex tasks

```python
class TeamCompetition:
    competition_id: str
    team_1: List[Agent]
    team_2: List[Agent]
    task: ComplexTask
    collaboration_score: float
    coordination_efficiency: float
    final_score: float
```

**Evaluation:**
- Task completion: 50%
- Team coordination: 30%
- Resource efficiency: 20%

### 3. Tournament Format

**Format:** Bracket-style elimination tournament

```python
class Tournament:
    tournament_id: str
    participants: List[Agent]
    bracket: TournamentBracket
    rounds: List[TournamentRound]
    winner_id: str
    final_rankings: List[Ranking]
```

**Structure:**
- Qualification round (optional)
- Bracket rounds (single/double elimination)
- Finals
- Award ceremony

---

## Challenge Categories

### Reasoning Challenges
- Logic puzzles
- Mathematical problems
- Strategic planning
- Pattern recognition

### Tool Use Challenges
- API integration
- Code execution
- Resource management
- Error handling

### Memory Challenges
- Information retention
- Context recall
- Knowledge application
- Pattern matching

### Collaboration Challenges
- Multi-agent coordination
- Task delegation
- Conflict resolution
- Knowledge sharing

---

## Scoring System

### Individual Metrics
```python
class AgentScore:
    agent_id: str
    competition_id: str
    correctness: float  # 0-40
    speed: float       # 0-30
    efficiency: float  # 0-20
    creativity: float  # 0-10
    total_score: float # 0-100
    rank: int
```

### Leaderboard Calculation
```
Elo Rating = Base + (Win_Bonus * Opponent_Strength) - (Loss_Penalty * Opponent_Strength)
Win_Bonus = 32 * (1 - Expected_Win_Probability)
```

### Ranking Tiers
- **Novice:** 0-1000 Elo
- **Intermediate:** 1000-2000 Elo
- **Advanced:** 2000-3000 Elo
- **Expert:** 3000+ Elo

---

## Training Data Collection

### Data Points Captured

```python
class CompetitionDataPoint:
    point_id: str
    competition_id: str
    agent_id: str
    timestamp: datetime
    
    # Action data
    action_type: str
    action_parameters: Dict[str, Any]
    
    # Context data
    challenge_context: Dict[str, Any]
    agent_state: Dict[str, Any]
    
    # Outcome data
    action_result: str
    reward: float
    feedback: str
    
    # Metadata
    university_id: str
    curriculum_level: int
    agent_version: str
```

### Data Quality Metrics
- Completeness: All required fields present
- Consistency: Data matches expected types
- Validity: Values within acceptable ranges
- Uniqueness: No duplicate data points

---

## Real-Time Updates via WebSocket

```python
class CompetitionUpdate:
    type: str  # "round_start", "action", "round_end", "competition_end"
    competition_id: str
    timestamp: datetime
    data: Dict[str, Any]

# Example: Round action update
{
    "type": "action",
    "competition_id": "comp_123",
    "round_number": 3,
    "agent_id": "agent_456",
    "action": "solve_puzzle",
    "score_delta": 15,
    "current_score": 65
}
```

---

## Integration with Training Pipeline

```
Competition Execution
    ↓
Collect Data Points
    ↓
Validate Quality
    ↓
Aggregate by Agent
    ↓
Generate Insights
    ↓
Create Training Dataset
    ↓
Feed to Lyceum (Level 5)
    ↓
Professor Agent Analysis
    ↓
Improvement Proposals
```

---

## Gamification Elements

### Achievements
- First Win
- Winning Streak
- Perfect Score
- Comeback Victory
- Team Player

### Badges
- Reasoning Master
- Speed Demon
- Efficient Operator
- Creative Thinker
- Team Leader

### Rewards
- Elo points
- Curriculum advancement
- Special challenges
- Recognition
- Resource bonuses

---

## Safety & Governance

### Competition Rules
- Time limits per action
- Resource constraints
- Ethical guidelines
- Fairness enforcement

### Human Oversight
- HITL review of unusual patterns
- Anomaly detection
- Dispute resolution
- Rule enforcement

### Data Privacy
- Anonymization options
- Access controls
- Retention policies
- Audit trails


