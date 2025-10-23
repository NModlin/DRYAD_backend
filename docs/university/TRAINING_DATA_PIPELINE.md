# Training Data Pipeline

**Version:** 1.0.0  
**Status:** Design Phase  
**Purpose:** Collect, process, and feed competition data to DRYAD evolution

---

## Pipeline Overview

```
Competition Execution
    ↓
Data Collection
    ↓
Data Validation
    ↓
Data Aggregation
    ↓
Dataset Generation
    ↓
Quality Assessment
    ↓
Feed to Lyceum (Level 5)
    ↓
Professor Agent Analysis
    ↓
Improvement Proposals
    ↓
System Evolution
```

---

## Stage 1: Data Collection

### Collection Points

```python
class DataCollectionPoint:
    """Captures data during competition"""
    
    # During action execution
    - agent_id: str
    - action_type: str
    - action_parameters: Dict[str, Any]
    - execution_time_ms: int
    - resource_usage: Dict[str, float]
    
    # During evaluation
    - correctness_score: float
    - efficiency_score: float
    - creativity_score: float
    - total_score: float
    
    # Context
    - challenge_context: Dict[str, Any]
    - agent_state: Dict[str, Any]
    - opponent_info: Dict[str, Any]
    
    # Outcome
    - action_result: str
    - reward: float
    - feedback: str
    - timestamp: datetime
```

### Collection Strategy

```python
class DataCollector:
    """Collects data from competitions"""
    
    async def collect_from_competition(
        self,
        competition_id: str
    ) -> List[DataPoint]:
        """Collect all data from competition"""
        
    async def collect_from_round(
        self,
        competition_id: str,
        round_number: int
    ) -> List[DataPoint]:
        """Collect data from specific round"""
        
    async def stream_data(
        self,
        competition_id: str
    ) -> AsyncIterator[DataPoint]:
        """Stream data as it's generated"""
```

---

## Stage 2: Data Validation

### Validation Rules

```python
class ValidationRule:
    """Defines validation criteria"""
    
    # Completeness
    required_fields: List[str]
    
    # Type checking
    field_types: Dict[str, type]
    
    # Range checking
    field_ranges: Dict[str, Tuple[float, float]]
    
    # Consistency
    consistency_checks: List[Callable]
    
    # Uniqueness
    unique_fields: List[str]

class DataValidator:
    async def validate(
        self,
        data_point: DataPoint
    ) -> ValidationResult:
        """Validate single data point"""
        
    async def validate_batch(
        self,
        data_points: List[DataPoint]
    ) -> ValidationReport:
        """Validate batch of data points"""
```

### Quality Metrics

```python
class QualityMetrics:
    completeness: float  # % of required fields present
    consistency: float   # % of consistent data
    validity: float      # % of valid values
    uniqueness: float    # % of unique records
    overall_score: float # Weighted average
```

---

## Stage 3: Data Aggregation

### Aggregation Strategy

```python
class DataAggregator:
    """Aggregates data from multiple sources"""
    
    async def aggregate_by_agent(
        self,
        agent_id: str,
        time_window: timedelta
    ) -> AgentDataset:
        """Aggregate data for specific agent"""
        
    async def aggregate_by_university(
        self,
        university_id: str,
        time_window: timedelta
    ) -> UniversityDataset:
        """Aggregate data for university"""
        
    async def aggregate_by_challenge(
        self,
        challenge_type: str,
        time_window: timedelta
    ) -> ChallengeDataset:
        """Aggregate data by challenge type"""
```

### Aggregation Levels

```python
class AggregationLevel:
    # Level 1: Individual actions
    individual_actions: List[DataPoint]
    
    # Level 2: Agent performance
    agent_performance: Dict[str, float]
    
    # Level 3: Competition results
    competition_results: Dict[str, Any]
    
    # Level 4: University insights
    university_insights: Dict[str, Any]
    
    # Level 5: System-wide patterns
    system_patterns: Dict[str, Any]
```

---

## Stage 4: Dataset Generation

### Dataset Types

```python
class TrainingDataset:
    dataset_id: str
    name: str
    description: str
    
    # Source information
    source_universities: List[str]
    source_competitions: List[str]
    time_period: Tuple[datetime, datetime]
    
    # Data statistics
    total_data_points: int
    agents_represented: int
    challenge_types: List[str]
    
    # Quality
    quality_score: float
    validation_report: ValidationReport
    
    # Status
    status: str  # "collecting", "validating", "ready", "in_use"
    created_at: datetime
    ready_at: Optional[datetime]
```

### Dataset Formats

```python
# Format 1: Raw data points
{
    "format": "raw",
    "data_points": [
        {"agent_id": "...", "action": "...", ...},
        ...
    ]
}

# Format 2: Aggregated statistics
{
    "format": "aggregated",
    "agent_stats": {
        "agent_123": {
            "avg_score": 85.5,
            "win_rate": 0.72,
            "improvement_trend": 0.05
        }
    }
}

# Format 3: Reinforcement learning format
{
    "format": "rl",
    "episodes": [
        {
            "state": {...},
            "action": {...},
            "reward": 15.0,
            "next_state": {...}
        }
    ]
}
```

---

## Stage 5: Quality Assessment

### Assessment Criteria

```python
class QualityAssessment:
    # Data quality
    completeness_score: float
    consistency_score: float
    validity_score: float
    
    # Statistical properties
    distribution_analysis: Dict[str, Any]
    outlier_detection: List[str]
    correlation_analysis: Dict[str, float]
    
    # Usefulness
    information_entropy: float
    diversity_score: float
    relevance_score: float
    
    # Overall
    ready_for_training: bool
    recommended_use_cases: List[str]
    warnings: List[str]
```

---

## Stage 6: Feed to Lyceum

### Integration with Level 5

```python
class LyceumIntegration:
    async def submit_dataset(
        self,
        dataset: TrainingDataset
    ) -> str:
        """Submit dataset to Lyceum"""
        
    async def get_improvement_proposals(
        self,
        dataset_id: str
    ) -> List[ImprovementProposal]:
        """Get proposals from Professor Agent"""
        
    async def track_improvements(
        self,
        dataset_id: str
    ) -> ImprovementTracking:
        """Track improvements from dataset"""
```

### Data Flow to Evolution

```
Training Dataset
    ↓
Professor Agent (Analyzer)
    ↓
Performance Analysis
    ↓
Hypothesis Generation
    ↓
Experiment Design
    ↓
Controlled Experiments
    ↓
Validation
    ↓
Improvement Proposals
    ↓
Human Review (HITL)
    ↓
Approved Improvements
    ↓
System Update
```

---

## Governance & Privacy

### Data Ownership

```python
class DataOwnership:
    dataset_id: str
    creating_university_id: str
    contributing_universities: List[str]
    collective_dryad_system: bool  # Shared with all
    
    # Usage rights
    can_use_for_training: bool
    can_share_with_other_universities: bool
    can_publish_insights: bool
    anonymization_required: bool
```

### Retention Policy

```python
class RetentionPolicy:
    raw_data_retention_days: int = 90
    aggregated_data_retention_days: int = 365
    insights_retention_days: int = 1825  # 5 years
    
    # Archival
    archive_after_days: int = 365
    delete_after_days: int = 2555  # 7 years
```

---

## Monitoring & Metrics

### Pipeline Metrics

```python
class PipelineMetrics:
    # Throughput
    data_points_per_second: float
    datasets_generated_per_day: int
    
    # Quality
    average_quality_score: float
    validation_pass_rate: float
    
    # Latency
    collection_to_ready_time_hours: float
    
    # Utilization
    datasets_in_use: int
    improvement_proposals_generated: int
```


