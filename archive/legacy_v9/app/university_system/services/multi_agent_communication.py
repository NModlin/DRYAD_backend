"""
Multi-Agent Communication System

This module handles inter-agent communication and coordination including:
- Broadcast messaging to multiple agents
- Task assignment negotiation
- Synchronous work coordination
- Consensus building
- Real-time collaboration setup
"""

import asyncio
import json
from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timezone
import uuid
import logging
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.university_system.database.models_university import (
    UniversityAgent, AgentCollaboration, ConversationSession
)

logger = logging.getLogger(__name__)

class MessageBus:
    """In-memory message bus for inter-agent communication"""
    
    def __init__(self):
        self.subscribers: Dict[str, List[callable]] = {}
        self.message_history: List[Dict[str, Any]] = []
    
    def subscribe(self, agent_id: str, callback: callable):
        """Subscribe an agent to receive messages"""
        if agent_id not in self.subscribers:
            self.subscribers[agent_id] = []
        self.subscribers[agent_id].append(callback)
    
    def unsubscribe(self, agent_id: str, callback: callable):
        """Unsubscribe an agent from messages"""
        if agent_id in self.subscribers and callback in self.subscribers[agent_id]:
            self.subscribers[agent_id].remove(callback)
    
    async def publish(self, message: Dict[str, Any]):
        """Publish a message to subscribers"""
        recipient_id = message.get('recipient_id')
        sender_id = message.get('sender_id')
        
        # Store message in history
        self.message_history.append({
            **message,
            'timestamp': datetime.now(timezone.utc),
            'message_id': str(uuid.uuid4())
        })
        
        # Send to specific recipient or broadcast
        if recipient_id:
            if recipient_id in self.subscribers:
                for callback in self.subscribers[recipient_id]:
                    await callback(message)
        else:
            # Broadcast to all subscribers except sender
            for agent_id, callbacks in self.subscribers.items():
                if agent_id != sender_id:
                    for callback in callbacks:
                        await callback(message)

# Global message bus instance
message_bus = MessageBus()

class MultiAgentCommunication:
    """Handles inter-agent communication and coordination"""
    
    def __init__(self, db: Session):
        self.db = db
        self.active_conversations: Dict[str, ConversationSession] = {}
    
    async def broadcast_message(self, from_agent: str, message: str, 
                              recipient_agents: List[str]) -> bool:
        """Send message to multiple agents
        
        Args:
            from_agent: ID of the sending agent
            message: Message content
            recipient_agents: List of agent IDs to receive the message
            
        Returns:
            Boolean indicating success of message delivery
        """
        try:
            # Create message object
            message_data = {
                'sender_id': from_agent,
                'message': message,
                'recipient_agents': recipient_agents,
                'message_type': 'broadcast',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            # Validate recipients exist
            valid_recipients = await self._validate_recipients(recipient_agents)
            
            if not valid_recipients:
                logger.warning(f"No valid recipients found for broadcast from {from_agent}")
                return False
            
            # Add to conversation history for each recipient
            for recipient_id in valid_recipients:
                await self._add_to_conversation_history(from_agent, recipient_id, message)
            
            # Publish message via message bus
            await message_bus.publish(message_data)
            
            logger.info(f"Broadcast message from {from_agent} to {len(valid_recipients)} agents")
            return True
            
        except Exception as e:
            logger.error(f"Error in broadcast message: {e}")
            return False
    
    async def negotiate_task_assignment(self, collaboration_id: str, 
                                      proposed_tasks: Dict[str, Any]) -> Dict[str, Any]:
        """Enable agents to negotiate task assignments
        
        Args:
            collaboration_id: ID of the collaboration session
            proposed_tasks: Dictionary of proposed task assignments
            
        Returns:
            Dictionary containing negotiation results and final assignments
        """
        try:
            # Get collaboration details
            collaboration = self.db.query(AgentCollaboration).filter(
                AgentCollaboration.id == collaboration_id
            ).first()
            
            if not collaboration:
                raise ValueError(f"Collaboration {collaboration_id} not found")
            
            team_agents = collaboration.participating_agents
            
            # Create negotiation session
            negotiation_id = str(uuid.uuid4())
            negotiation_session = {
                'id': negotiation_id,
                'collaboration_id': collaboration_id,
                'proposed_tasks': proposed_tasks,
                'agent_preferences': {},
                'negotiation_status': 'active',
                'started_at': datetime.now(timezone.utc)
            }
            
            # Collect agent preferences for tasks
            agent_preferences = await self._collect_agent_preferences(
                team_agents, proposed_tasks
            )
            negotiation_session['agent_preferences'] = agent_preferences
            
            # Analyze preferences and optimize assignments
            optimized_assignments = self._optimize_task_assignments(
                proposed_tasks, agent_preferences
            )
            
            # Get final agreement from app.university_system.agents
            final_agreement = await self._reach_task_agreement(
                team_agents, optimized_assignments
            )
            
            negotiation_session['final_assignments'] = final_agreement
            negotiation_session['negotiation_status'] = 'completed'
            negotiation_session['completed_at'] = datetime.now(timezone.utc)
            
            logger.info(f"Task assignment negotiation completed for collaboration {collaboration_id}")
            return {
                'negotiation_id': negotiation_id,
                'proposed_tasks': proposed_tasks,
                'agent_preferences': agent_preferences,
                'final_assignments': final_agreement,
                'status': 'completed'
            }
            
        except Exception as e:
            logger.error(f"Error in task assignment negotiation: {e}")
            return {}
    
    async def coordinate_synchronous_work(self, collaboration_id: str, 
                                        coordination_type: str) -> Dict[str, Any]:
        """Coordinate agents working simultaneously on shared tasks
        
        Args:
            collaboration_id: ID of the collaboration session
            coordination_type: Type of coordination (parallel, sequential, hybrid)
            
        Returns:
            Dictionary containing coordination plan and status
        """
        try:
            # Get collaboration details
            collaboration = self.db.query(AgentCollaboration).filter(
                AgentCollaboration.id == collaboration_id
            ).first()
            
            if not collaboration:
                raise ValueError(f"Collaboration {collaboration_id} not found")
            
            team_agents = collaboration.participating_agents
            
            # Create coordination plan
            coordination_plan = {
                'collaboration_id': collaboration_id,
                'coordination_type': coordination_type,
                'team_agents': team_agents,
                'work_sessions': [],
                'synchronization_points': [],
                'status': 'initialized',
                'created_at': datetime.now(timezone.utc)
            }
            
            if coordination_type == 'parallel':
                coordination_plan['work_sessions'] = await self._create_parallel_sessions(
                    team_agents, collaboration.collaboration_goal
                )
            elif coordination_type == 'sequential':
                coordination_plan['work_sessions'] = await self._create_sequential_sessions(
                    team_agents, collaboration.collaboration_goal
                )
            elif coordination_type == 'hybrid':
                coordination_plan['work_sessions'] = await self._create_hybrid_sessions(
                    team_agents, collaboration.collaboration_goal
                )
            
            # Set up synchronization points
            coordination_plan['synchronization_points'] = self._define_synchronization_points(
                coordination_plan['work_sessions']
            )
            
            # Start coordination
            coordination_plan['status'] = 'active'
            coordination_plan['started_at'] = datetime.now(timezone.utc)
            
            # Notify all agents about coordination plan
            await self._notify_team_of_coordination(team_agents, coordination_plan)
            
            logger.info(f"Synchronous work coordination started for collaboration {collaboration_id}")
            return coordination_plan
            
        except Exception as e:
            logger.error(f"Error coordinating synchronous work: {e}")
            return {}
    
    async def facilitate_consensus_building(self, collaboration_id: str, 
                                          decision_points: List[str]) -> Dict[str, Any]:
        """Help agents build consensus on important decisions
        
        Args:
            collaboration_id: ID of the collaboration session
            decision_points: List of decision points requiring consensus
            
        Returns:
            Dictionary containing consensus building process and results
        """
        try:
            # Get collaboration details
            collaboration = self.db.query(AgentCollaboration).filter(
                AgentCollaboration.id == collaboration_id
            ).first()
            
            if not collaboration:
                raise ValueError(f"Collaboration {collaboration_id} not found")
            
            team_agents = collaboration.participating_agents
            consensus_id = str(uuid.uuid4())
            
            # Initialize consensus building process
            consensus_process = {
                'consensus_id': consensus_id,
                'collaboration_id': collaboration_id,
                'decision_points': decision_points,
                'team_agents': team_agents,
                'consensus_rounds': {},
                'status': 'active',
                'started_at': datetime.now(timezone.utc)
            }
            
            # Process each decision point
            for decision_point in decision_points:
                round_result = await self._process_decision_round(
                    team_agents, decision_point
                )
                consensus_process['consensus_rounds'][decision_point] = round_result
                
                # Check if consensus reached
                if round_result['consensus_reached']:
                    logger.info(f"Consensus reached for decision: {decision_point}")
                else:
                    # Continue to next round if needed
                    logger.info(f"No consensus yet for decision: {decision_point}, continuing rounds")
            
            consensus_process['status'] = 'completed'
            consensus_process['completed_at'] = datetime.now(timezone.utc)
            
            # Store final consensus results
            final_decisions = {}
            for decision_point, round_data in consensus_process['consensus_rounds'].items():
                final_decisions[decision_point] = round_data['final_decision']
            
            consensus_process['final_decisions'] = final_decisions
            
            logger.info(f"Consensus building completed for collaboration {collaboration_id}")
            return consensus_process
            
        except Exception as e:
            logger.error(f"Error facilitating consensus building: {e}")
            return {}
    
    async def enable_real_time_collaboration(self, collaboration_id: str) -> Dict[str, Any]:
        """Set up real-time collaboration environment
        
        Args:
            collaboration_id: ID of the collaboration session
            
        Returns:
            Dictionary containing real-time collaboration setup and connection details
        """
        try:
            # Get collaboration details
            collaboration = self.db.query(AgentCollaboration).filter(
                AgentCollaboration.id == collaboration_id
            ).first()
            
            if not collaboration:
                raise ValueError(f"Collaboration {collaboration_id} not found")
            
            team_agents = collaboration.participating_agents
            
            # Create real-time collaboration workspace
            workspace_id = str(uuid.uuid4())
            collaboration_workspace = {
                'workspace_id': workspace_id,
                'collaboration_id': collaboration_id,
                'team_agents': team_agents,
                'real_time_features': {
                    'shared_whiteboard': True,
                    'live_chat': True,
                    'screen_sharing': True,
                    'document_collaboration': True,
                    'voice_chat': False,  # Can be enabled based on capabilities
                    'video_chat': False   # Can be enabled based on capabilities
                },
                'connection_details': {
                    'websocket_endpoint': f"/ws/collaboration/{workspace_id}",
                    'api_endpoint': f"/api/v1/collaboration/{collaboration_id}",
                    'sync_frequency': 'real-time',
                    'max_concurrent_users': len(team_agents)
                },
                'status': 'active',
                'created_at': datetime.now(timezone.utc)
            }
            
            # Set up real-time subscriptions
            for agent_id in team_agents:
                message_bus.subscribe(agent_id, self._handle_real_time_message)
            
            # Notify agents of workspace availability
            await self._notify_team_of_workspace(team_agents, collaboration_workspace)
            
            logger.info(f"Real-time collaboration enabled for collaboration {collaboration_id}")
            return collaboration_workspace
            
        except Exception as e:
            logger.error(f"Error enabling real-time collaboration: {e}")
            return {}
    
    # Helper methods
    
    async def _validate_recipients(self, recipient_ids: List[str]) -> List[str]:
        """Validate that recipient agents exist and are active"""
        valid_recipients = []
        
        for agent_id in recipient_ids:
            agent = self.db.query(UniversityAgent).filter(
                and_(
                    UniversityAgent.id == agent_id,
                    UniversityAgent.status == 'active'
                )
            ).first()
            
            if agent:
                valid_recipients.append(agent_id)
        
        return valid_recipients
    
    async def _add_to_conversation_history(self, sender_id: str, recipient_id: str, 
                                         message: str):
        """Add message to conversation history for both agents"""
        # Get or create conversation session for each agent
        for agent_id in [sender_id, recipient_id]:
            session_key = f"{agent_id}_global"
            
            if session_key not in self.active_conversations:
                # Create new conversation session
                session = ConversationSession(
                    id=str(uuid.uuid4()),
                    agent_id=agent_id,
                    session_type="collaboration",
                    context_data={'collaboration_type': 'global'},
                    conversation_history=[]
                )
                self.db.add(session)
                self.active_conversations[session_key] = session
            else:
                session = self.active_conversations[session_key]
            
            # Add message to history
            message_entry = {
                'sender_id': sender_id,
                'message': message,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'message_type': 'collaboration'
            }
            session.conversation_history.append(message_entry)
        
        self.db.commit()
    
    async def _collect_agent_preferences(self, agent_ids: List[str], 
                                       proposed_tasks: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Collect agent preferences for task assignments"""
        preferences = {}
        
        for agent_id in agent_ids:
            agent_preferences = {
                'preferred_tasks': [],
                'task_capacity': 1,  # Default capacity
                'skill_matches': [],
                'availability': True
            }
            
            # In a real implementation, this would query the agent's preferences
            # For now, we'll simulate preference collection
            for task_name, task_details in proposed_tasks.items():
                # Simulate agent preference scoring
                preference_score = 0.7  # Default preference
                agent_preferences['preferred_tasks'].append({
                    'task_name': task_name,
                    'preference_score': preference_score,
                    'estimated_completion_time': task_details.get('estimated_hours', 1)
                })
            
            preferences[agent_id] = agent_preferences
        
        return preferences
    
    def _optimize_task_assignments(self, proposed_tasks: Dict[str, Any], 
                                 agent_preferences: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Optimize task assignments based on agent preferences"""
        optimized_assignments = {}
        
        # Simple optimization logic
        for agent_id, preferences in agent_preferences.items():
            assigned_tasks = []
            
            for task_pref in preferences['preferred_tasks']:
                if task_pref['preference_score'] > 0.5:  # Threshold for assignment
                    assigned_tasks.append({
                        'task_name': task_pref['task_name'],
                        'estimated_time': task_pref['estimated_completion_time'],
                        'assignment_reason': 'preference_match'
                    })
            
            optimized_assignments[agent_id] = assigned_tasks
        
        return optimized_assignments
    
    async def _reach_task_agreement(self, team_agents: List[str], 
                                  assignments: Dict[str, Any]) -> Dict[str, Any]:
        """Reach final agreement on task assignments"""
        # Simulate agent agreement process
        agreement = {
            'assignments': assignments,
            'agreement_status': 'consensus_reached',
            'agreement_timestamp': datetime.now(timezone.utc).isoformat(),
            'consensus_score': 0.85  # High consensus score
        }
        
        return agreement
    
    async def _create_parallel_sessions(self, team_agents: List[str], 
                                      goal: str) -> List[Dict[str, Any]]:
        """Create parallel work sessions for team members"""
        sessions = []
        
        for i, agent_id in enumerate(team_agents):
            session = {
                'session_id': str(uuid.uuid4()),
                'agent_id': agent_id,
                'session_type': 'parallel',
                'work_focus': f"Task_{i+1}",
                'estimated_duration': 60,  # minutes
                'dependencies': [],  # No dependencies in parallel work
                'synchronization_point': 'midpoint_check'
            }
            sessions.append(session)
        
        return sessions
    
    async def _create_sequential_sessions(self, team_agents: List[str], 
                                        goal: str) -> List[Dict[str, Any]]:
        """Create sequential work sessions for team members"""
        sessions = []
        
        for i, agent_id in enumerate(team_agents):
            session = {
                'session_id': str(uuid.uuid4()),
                'agent_id': agent_id,
                'session_type': 'sequential',
                'work_focus': f"Phase_{i+1}",
                'estimated_duration': 90,  # minutes
                'dependencies': [team_agents[i-1]] if i > 0 else [],  # Depends on previous agent
                'synchronization_point': 'end_of_phase'
            }
            sessions.append(session)
        
        return sessions
    
    async def _create_hybrid_sessions(self, team_agents: List[str], 
                                    goal: str) -> List[Dict[str, Any]]:
        """Create hybrid work sessions combining parallel and sequential work"""
        sessions = []
        
        # Split team into subgroups for parallel work
        mid_point = len(team_agents) // 2
        subgroup1 = team_agents[:mid_point]
        subgroup2 = team_agents[mid_point:]
        
        # Subgroup 1 - parallel work
        for i, agent_id in enumerate(subgroup1):
            session = {
                'session_id': str(uuid.uuid4()),
                'agent_id': agent_id,
                'session_type': 'parallel',
                'work_focus': f"Research_Phase_{i+1}",
                'estimated_duration': 60,
                'dependencies': [],
                'synchronization_point': 'research_complete'
            }
            sessions.append(session)
        
        # Subgroup 2 - depends on subgroup 1 completion
        for i, agent_id in enumerate(subgroup2):
            session = {
                'session_id': str(uuid.uuid4()),
                'agent_id': agent_id,
                'session_type': 'sequential',
                'work_focus': f"Analysis_Phase_{i+1}",
                'estimated_duration': 90,
                'dependencies': subgroup1,  # Depends on all of subgroup 1
                'synchronization_point': 'analysis_complete'
            }
            sessions.append(session)
        
        return sessions
    
    def _define_synchronization_points(self, work_sessions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Define synchronization points for coordinating work sessions"""
        sync_points = []
        
        # Identify key synchronization moments
        sync_points.append({
            'point_id': str(uuid.uuid4()),
            'point_name': 'initial_kickoff',
            'timing': 'start',
            'participants': 'all',
            'purpose': 'coordinate starting point'
        })
        
        sync_points.append({
            'point_id': str(uuid.uuid4()),
            'point_name': 'midpoint_review',
            'timing': 'middle',
            'participants': 'all',
            'purpose': 'review progress and adjust if needed'
        })
        
        sync_points.append({
            'point_id': str(uuid.uuid4()),
            'point_name': 'final_integration',
            'timing': 'end',
            'participants': 'all',
            'purpose': 'integrate and finalize work'
        })
        
        return sync_points
    
    async def _notify_team_of_coordination(self, team_agents: List[str], 
                                         coordination_plan: Dict[str, Any]):
        """Notify team members about coordination plan"""
        for agent_id in team_agents:
            notification = {
                'type': 'coordination_plan',
                'agent_id': agent_id,
                'plan': coordination_plan,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            await message_bus.publish(notification)
    
    async def _process_decision_round(self, team_agents: List[str], 
                                    decision_point: str) -> Dict[str, Any]:
        """Process a single round of decision making for consensus"""
        # Collect initial positions from all agents
        agent_positions = {}
        
        for agent_id in team_agents:
            # In real implementation, this would query the agent's position
            # For now, simulate position collection
            position = f"Position_on_{decision_point}"
            agent_positions[agent_id] = {
                'position': position,
                'reasoning': f"Agent {agent_id} reasoning for position",
                'flexibility': 0.7  # How flexible the agent is (0-1)
            }
        
        # Analyze positions for consensus potential
        consensus_analysis = self._analyze_consensus_potential(agent_positions)
        
        if consensus_analysis['consensus_likelihood'] > 0.8:
            # High consensus likelihood - try to reach agreement
            final_decision = self._reach_consensus(agent_positions)
            return {
                'decision_point': decision_point,
                'agent_positions': agent_positions,
                'consensus_reached': True,
                'final_decision': final_decision,
                'consensus_score': consensus_analysis['consensus_likelihood']
            }
        else:
            # Low consensus - propose compromise or continue rounds
            compromise_proposal = self._propose_compromise(agent_positions)
            return {
                'decision_point': decision_point,
                'agent_positions': agent_positions,
                'consensus_reached': False,
                'compromise_proposal': compromise_proposal,
                'consensus_score': consensus_analysis['consensus_likelihood'],
                'next_round_needed': True
            }
    
    def _analyze_consensus_potential(self, agent_positions: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze the potential for reaching consensus"""
        # Simple consensus analysis
        positions = [pos['position'] for pos in agent_positions.values()]
        flexibilities = [pos['flexibility'] for pos in agent_positions.values()]
        
        # Check if all positions are similar (simplified)
        unique_positions = len(set(positions))
        total_agents = len(positions)
        
        consensus_likelihood = max(0.0, 1.0 - (unique_positions - 1) / max(total_agents - 1, 1))
        
        # Adjust for flexibility
        avg_flexibility = sum(flexibilities) / len(flexibilities)
        consensus_likelihood *= avg_flexibility
        
        return {
            'consensus_likelihood': consensus_likelihood,
            'unique_positions': unique_positions,
            'average_flexibility': avg_flexibility
        }
    
    def _reach_consensus(self, agent_positions: Dict[str, Dict[str, Any]]) -> str:
        """Reach consensus among agent positions"""
        # Simple consensus logic - choose the most flexible position or average
        positions = list(agent_positions.keys())
        return f"Consensus_{positions[0]}_and_{positions[1]}_agreement"
    
    def _propose_compromise(self, agent_positions: Dict[str, Dict[str, Any]]) -> str:
        """Propose a compromise based on agent positions"""
        return f"Compromise_proposal_based_on_agent_positions"
    
    async def _notify_team_of_workspace(self, team_agents: List[str], 
                                      workspace: Dict[str, Any]):
        """Notify team about workspace availability"""
        for agent_id in team_agents:
            notification = {
                'type': 'workspace_ready',
                'agent_id': agent_id,
                'workspace': workspace,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            await message_bus.publish(notification)
    
    async def _handle_real_time_message(self, message: Dict[str, Any]):
        """Handle incoming real-time messages"""
        # This would handle real-time message processing
        logger.debug(f"Received real-time message: {message.get('message_type', 'unknown')}")