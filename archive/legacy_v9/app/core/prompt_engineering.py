"""
Advanced Prompt Engineering and Chain-of-Thought Reasoning System
Implements sophisticated prompt templates, reasoning chains, and context-aware conversation management.
"""

import json
import re
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

from app.core.logging_config import get_logger
from app.core.llm_config import get_llm, get_llm_info

logger = get_logger(__name__)


class ReasoningType(str, Enum):
    """Types of reasoning patterns."""
    CHAIN_OF_THOUGHT = "chain_of_thought"
    STEP_BY_STEP = "step_by_step"
    PROBLEM_SOLVING = "problem_solving"
    ANALYTICAL = "analytical"
    CREATIVE = "creative"
    COMPARATIVE = "comparative"
    CAUSAL = "causal"
    DEDUCTIVE = "deductive"
    INDUCTIVE = "inductive"


class PromptTemplate(str, Enum):
    """Pre-defined prompt templates."""
    RESEARCH_ANALYSIS = "research_analysis"
    CONTENT_GENERATION = "content_generation"
    PROBLEM_SOLVING = "problem_solving"
    DECISION_MAKING = "decision_making"
    CREATIVE_WRITING = "creative_writing"
    TECHNICAL_EXPLANATION = "technical_explanation"
    COMPARATIVE_ANALYSIS = "comparative_analysis"
    SYNTHESIS = "synthesis"


@dataclass
class ReasoningStep:
    """Individual step in a reasoning chain."""
    step_number: int
    description: str
    input_data: Dict[str, Any]
    reasoning: str
    output: str
    confidence: float
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ChainOfThoughtResult:
    """Result of chain-of-thought reasoning."""
    query: str
    reasoning_type: ReasoningType
    steps: List[ReasoningStep]
    final_answer: str
    confidence_score: float
    execution_time: float
    metadata: Dict[str, Any]


class AdvancedPromptEngine:
    """Advanced prompt engineering system with chain-of-thought reasoning."""
    
    def __init__(self):
        self.prompt_templates = self._initialize_prompt_templates()
        self.reasoning_patterns = self._initialize_reasoning_patterns()
        self.context_memory = {}
        
    def _initialize_prompt_templates(self) -> Dict[str, str]:
        """Initialize sophisticated prompt templates."""
        return {
            PromptTemplate.RESEARCH_ANALYSIS: """
You are an expert researcher conducting a comprehensive analysis. Follow this structured approach:

**Research Query:** {query}
**Context:** {context}

**Step-by-Step Analysis:**
1. **Understanding the Query**
   - Break down the key components
   - Identify the scope and objectives
   - Note any constraints or requirements

2. **Information Gathering**
   - Identify relevant sources and data points
   - Consider multiple perspectives
   - Evaluate information quality and reliability

3. **Analysis and Synthesis**
   - Analyze patterns and relationships
   - Draw connections between concepts
   - Identify key insights and implications

4. **Conclusion and Recommendations**
   - Summarize key findings
   - Provide actionable recommendations
   - Suggest areas for further investigation

**Please provide a detailed response following this structure.**
            """,
            
            PromptTemplate.PROBLEM_SOLVING: """
You are an expert problem solver. Use systematic reasoning to address this challenge:

**Problem:** {problem}
**Context:** {context}
**Constraints:** {constraints}

**Chain-of-Thought Problem Solving:**

1. **Problem Definition**
   - Clearly state the problem
   - Identify root causes
   - Define success criteria

2. **Solution Generation**
   - Brainstorm multiple approaches
   - Consider creative alternatives
   - Evaluate feasibility of each option

3. **Analysis and Evaluation**
   - Assess pros and cons of each solution
   - Consider implementation challenges
   - Evaluate potential outcomes

4. **Recommendation**
   - Select the best solution
   - Provide detailed implementation plan
   - Identify potential risks and mitigation strategies

**Think through each step carefully and show your reasoning.**
            """,
            
            PromptTemplate.DECISION_MAKING: """
You are a strategic decision maker. Analyze this situation systematically:

**Decision Context:** {context}
**Options:** {options}
**Criteria:** {criteria}

**Decision Analysis Framework:**

1. **Situation Assessment**
   - Understand the current state
   - Identify key stakeholders
   - Clarify decision objectives

2. **Option Evaluation**
   For each option, analyze:
   - Alignment with objectives
   - Resource requirements
   - Risk assessment
   - Expected outcomes

3. **Criteria-Based Analysis**
   - Weight each criterion by importance
   - Score each option against criteria
   - Calculate overall scores

4. **Final Recommendation**
   - Recommend the best option
   - Explain the reasoning
   - Address potential concerns
   - Suggest implementation approach

**Provide a thorough analysis with clear reasoning.**
            """,
            
            PromptTemplate.TECHNICAL_EXPLANATION: """
You are a technical expert providing clear explanations. Structure your response as follows:

**Topic:** {topic}
**Audience Level:** {audience_level}
**Context:** {context}

**Structured Technical Explanation:**

1. **Overview and Introduction**
   - Provide a clear, concise overview
   - Explain why this topic is important
   - Set the context for the explanation

2. **Core Concepts**
   - Break down complex ideas into digestible parts
   - Use analogies and examples where helpful
   - Define technical terms clearly

3. **Detailed Explanation**
   - Explain how things work step-by-step
   - Show relationships between components
   - Provide concrete examples

4. **Practical Applications**
   - Demonstrate real-world usage
   - Explain benefits and limitations
   - Suggest next steps for learning

**Adapt your language to the audience level while maintaining accuracy.**
            """,
            
            PromptTemplate.SYNTHESIS: """
You are synthesizing information from multiple sources. Follow this comprehensive approach:

**Synthesis Goal:** {goal}
**Sources:** {sources}
**Focus Areas:** {focus_areas}

**Information Synthesis Process:**

1. **Source Analysis**
   - Evaluate each source for relevance and credibility
   - Identify key themes and insights
   - Note any conflicting information

2. **Pattern Recognition**
   - Find common themes across sources
   - Identify unique perspectives
   - Recognize emerging trends

3. **Integration and Synthesis**
   - Combine insights into a coherent narrative
   - Resolve conflicts and contradictions
   - Create new understanding from combined information

4. **Conclusions and Implications**
   - Draw meaningful conclusions
   - Identify implications and applications
   - Suggest areas for further exploration

**Create a comprehensive synthesis that adds value beyond individual sources.**
            """
        }
    
    def _initialize_reasoning_patterns(self) -> Dict[ReasoningType, str]:
        """Initialize reasoning pattern templates."""
        return {
            ReasoningType.CHAIN_OF_THOUGHT: """
Let me think through this step by step:

Step 1: {step1_description}
Reasoning: {step1_reasoning}
Conclusion: {step1_conclusion}

Step 2: {step2_description}
Reasoning: {step2_reasoning}
Conclusion: {step2_conclusion}

[Continue for additional steps...]

Final Answer: Based on this chain of reasoning, {final_answer}
            """,
            
            ReasoningType.PROBLEM_SOLVING: """
Problem-Solving Approach:

1. Problem Understanding:
   - What exactly needs to be solved?
   - What are the constraints?
   - What does success look like?

2. Solution Generation:
   - What are possible approaches?
   - What resources are available?
   - What are the trade-offs?

3. Solution Evaluation:
   - Which approach is most feasible?
   - What are the risks?
   - How can we measure success?

4. Implementation Plan:
   - What are the specific steps?
   - What could go wrong?
   - How do we adapt if needed?
            """,
            
            ReasoningType.ANALYTICAL: """
Analytical Framework:

1. Data Gathering:
   - What information do we have?
   - What information do we need?
   - How reliable are our sources?

2. Pattern Analysis:
   - What patterns emerge from the data?
   - What relationships can we identify?
   - What anomalies or outliers exist?

3. Hypothesis Formation:
   - What explanations fit the patterns?
   - What predictions can we make?
   - How can we test our hypotheses?

4. Conclusion Drawing:
   - What does the analysis reveal?
   - How confident are we in our conclusions?
   - What are the implications?
            """
        }
    
    async def generate_chain_of_thought_response(
        self,
        query: str,
        reasoning_type: ReasoningType = ReasoningType.CHAIN_OF_THOUGHT,
        context: Optional[str] = None,
        max_steps: int = 5
    ) -> ChainOfThoughtResult:
        """Generate a response using chain-of-thought reasoning."""
        import time
        start_time = time.time()
        
        try:
            # Get LLM instance
            llm = get_llm()
            if not llm:
                raise ValueError("No LLM available for chain-of-thought reasoning")
            
            # Create chain-of-thought prompt
            cot_prompt = self._create_chain_of_thought_prompt(query, reasoning_type, context)
            
            # Generate response
            response = llm.invoke(cot_prompt)
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            # Parse reasoning steps
            steps = self._parse_reasoning_steps(response_text)
            
            # Extract final answer
            final_answer = self._extract_final_answer(response_text)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(steps, response_text)
            
            execution_time = time.time() - start_time
            
            return ChainOfThoughtResult(
                query=query,
                reasoning_type=reasoning_type,
                steps=steps,
                final_answer=final_answer,
                confidence_score=confidence_score,
                execution_time=execution_time,
                metadata={
                    "context_provided": context is not None,
                    "steps_generated": len(steps),
                    "reasoning_pattern": reasoning_type.value
                }
            )
            
        except Exception as e:
            logger.error(f"Chain-of-thought reasoning failed: {e}")
            execution_time = time.time() - start_time
            
            return ChainOfThoughtResult(
                query=query,
                reasoning_type=reasoning_type,
                steps=[],
                final_answer=f"Unable to generate chain-of-thought response: {str(e)}",
                confidence_score=0.0,
                execution_time=execution_time,
                metadata={"error": str(e)}
            )
    
    def _create_chain_of_thought_prompt(
        self,
        query: str,
        reasoning_type: ReasoningType,
        context: Optional[str] = None
    ) -> str:
        """Create a chain-of-thought reasoning prompt."""
        base_prompt = f"""
You are an expert reasoner. Please think through this query step by step using {reasoning_type.value} reasoning.

Query: {query}
"""
        
        if context:
            base_prompt += f"\nContext: {context}\n"
        
        base_prompt += f"""
Please follow this reasoning approach:
{self.reasoning_patterns.get(reasoning_type, self.reasoning_patterns[ReasoningType.CHAIN_OF_THOUGHT])}

Show your work clearly, explaining each step of your reasoning process.
"""
        
        return base_prompt
    
    def _parse_reasoning_steps(self, response_text: str) -> List[ReasoningStep]:
        """Parse reasoning steps from the response."""
        steps = []
        
        # Simple pattern matching for steps (can be enhanced)
        step_pattern = r'Step (\d+):(.*?)(?=Step \d+:|Final Answer:|$)'
        matches = re.findall(step_pattern, response_text, re.DOTALL | re.IGNORECASE)
        
        for i, (step_num, step_content) in enumerate(matches):
            steps.append(ReasoningStep(
                step_number=int(step_num),
                description=f"Step {step_num}",
                input_data={},
                reasoning=step_content.strip(),
                output=step_content.strip()[:100] + "...",
                confidence=0.8,  # Default confidence
                metadata={"parsed_from_response": True}
            ))
        
        return steps
    
    def _extract_final_answer(self, response_text: str) -> str:
        """Extract the final answer from the response."""
        # Look for final answer patterns
        patterns = [
            r'Final Answer:\s*(.*?)(?:\n|$)',
            r'Conclusion:\s*(.*?)(?:\n|$)',
            r'Therefore,\s*(.*?)(?:\n|$)',
            r'In conclusion,\s*(.*?)(?:\n|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response_text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()
        
        # If no specific pattern found, return last paragraph
        paragraphs = response_text.strip().split('\n\n')
        return paragraphs[-1] if paragraphs else response_text[:200] + "..."
    
    def _calculate_confidence_score(self, steps: List[ReasoningStep], response_text: str) -> float:
        """Calculate confidence score based on reasoning quality."""
        base_score = 0.7
        
        # Adjust based on number of reasoning steps
        if len(steps) >= 3:
            base_score += 0.1
        
        # Adjust based on response length (more detailed = higher confidence)
        if len(response_text) > 500:
            base_score += 0.1
        
        # Adjust based on presence of specific reasoning indicators
        reasoning_indicators = ['because', 'therefore', 'since', 'given that', 'as a result']
        indicator_count = sum(1 for indicator in reasoning_indicators if indicator in response_text.lower())
        base_score += min(indicator_count * 0.02, 0.1)
        
        return min(base_score, 1.0)


# Global instance
prompt_engine = AdvancedPromptEngine()
