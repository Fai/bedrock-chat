"""
Multi-agent orchestration patterns and communication protocols.

Implements advanced orchestration patterns including pipeline, broadcast,
and collaborative decision making for complex multi-agent scenarios.
"""

import logging
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
from dataclasses import dataclass

from app.agents.multi_agent.hierarchy import AgentHierarchy
from app.agents.multi_agent.swarm import AgentSwarm, SwarmTask

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class OrchestrationPattern(Enum):
    """Multi-agent orchestration patterns."""
    PIPELINE = "pipeline"
    BROADCAST = "broadcast"
    COLLABORATIVE = "collaborative"
    COMPETITIVE = "competitive"


@dataclass
class AgentMessage:
    """Message for agent-to-agent communication."""
    sender_id: str
    receiver_id: str
    message_type: str
    content: Any
    timestamp: float
    requires_response: bool = False


class MultiAgentOrchestrator:
    """
    Advanced multi-agent orchestrator with multiple coordination patterns.
    """
    
    def __init__(self, orchestrator_id: str):
        """
        Initialize multi-agent orchestrator.
        
        Args:
            orchestrator_id: Unique orchestrator identifier
        """
        self.orchestrator_id = orchestrator_id
        self.hierarchies: Dict[str, AgentHierarchy] = {}
        self.swarms: Dict[str, AgentSwarm] = {}
        self.message_queue: List[AgentMessage] = []
        
        logger.info(f"Initialized multi-agent orchestrator {orchestrator_id}")
    
    def add_hierarchy(self, hierarchy_id: str, hierarchy: AgentHierarchy) -> None:
        """Add agent hierarchy to orchestrator."""
        self.hierarchies[hierarchy_id] = hierarchy
        logger.info(f"Added hierarchy {hierarchy_id} to orchestrator")
    
    def add_swarm(self, swarm_id: str, swarm: AgentSwarm) -> None:
        """Add agent swarm to orchestrator."""
        self.swarms[swarm_id] = swarm
        logger.info(f"Added swarm {swarm_id} to orchestrator")
    
    def execute_pattern(
        self, 
        pattern: OrchestrationPattern, 
        task: str, 
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Execute multi-agent task using specified orchestration pattern.
        
        Args:
            pattern: Orchestration pattern to use
            task: Task description
            context: Optional task context
            
        Returns:
            Orchestration result
        """
        logger.info(f"Executing {pattern.value} pattern for task: {task}")
        
        if pattern == OrchestrationPattern.PIPELINE:
            return self._execute_pipeline(task, context or {})
        elif pattern == OrchestrationPattern.BROADCAST:
            return self._execute_broadcast(task, context or {})
        elif pattern == OrchestrationPattern.COLLABORATIVE:
            return self._execute_collaborative(task, context or {})
        elif pattern == OrchestrationPattern.COMPETITIVE:
            return self._execute_competitive(task, context or {})
        else:
            raise ValueError(f"Unknown orchestration pattern: {pattern}")
    
    def _execute_pipeline(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute pipeline pattern: sequential processing through agents."""
        pipeline_results = []
        current_input = task
        
        # Process through hierarchies first
        for hierarchy_id, hierarchy in self.hierarchies.items():
            result = hierarchy.coordinate_task(current_input, context)
            pipeline_results.append({
                "stage": f"hierarchy_{hierarchy_id}",
                "input": current_input,
                "result": result
            })
            current_input = result.get("final_result", {}).get("synthesized_response", current_input)
        
        # Then through swarms
        for swarm_id, swarm in self.swarms.items():
            swarm_tasks = [SwarmTask(f"pipeline_{swarm_id}", current_input)]
            result = swarm.execute_parallel_tasks(swarm_tasks)
            pipeline_results.append({
                "stage": f"swarm_{swarm_id}",
                "input": current_input,
                "result": result
            })
            # Extract result for next stage
            if result.get("agent_results"):
                first_agent_result = next(iter(result["agent_results"].values()))
                if first_agent_result.get("results"):
                    current_input = first_agent_result["results"][0].get("result", current_input)
        
        return {
            "pattern": "pipeline",
            "original_task": task,
            "pipeline_stages": len(pipeline_results),
            "pipeline_results": pipeline_results,
            "final_output": current_input
        }
    
    def _execute_broadcast(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute broadcast pattern: parallel processing across all agents."""
        broadcast_results = {}
        
        # Broadcast to all hierarchies
        for hierarchy_id, hierarchy in self.hierarchies.items():
            result = hierarchy.coordinate_task(task, context)
            broadcast_results[f"hierarchy_{hierarchy_id}"] = result
        
        # Broadcast to all swarms
        for swarm_id, swarm in self.swarms.items():
            swarm_tasks = [SwarmTask(f"broadcast_{swarm_id}", task)]
            result = swarm.execute_parallel_tasks(swarm_tasks)
            broadcast_results[f"swarm_{swarm_id}"] = result
        
        # Aggregate results
        aggregated_result = self._aggregate_broadcast_results(broadcast_results)
        
        return {
            "pattern": "broadcast",
            "original_task": task,
            "broadcast_targets": len(broadcast_results),
            "broadcast_results": broadcast_results,
            "aggregated_result": aggregated_result
        }
    
    def _execute_collaborative(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute collaborative pattern: agents work together with communication."""
        collaboration_results = []
        
        # Phase 1: Initial analysis by hierarchies
        initial_analyses = {}
        for hierarchy_id, hierarchy in self.hierarchies.items():
            analysis = hierarchy.coordinate_task(f"Analyze: {task}", context)
            initial_analyses[hierarchy_id] = analysis
        
        # Phase 2: Cross-pollination via message passing
        messages = self._generate_collaboration_messages(initial_analyses)
        self.message_queue.extend(messages)
        
        # Phase 3: Collaborative refinement
        for hierarchy_id, hierarchy in self.hierarchies.items():
            # Include insights from other agents
            collaborative_context = context.copy()
            collaborative_context["peer_insights"] = {
                k: v for k, v in initial_analyses.items() if k != hierarchy_id
            }
            
            refined_result = hierarchy.coordinate_task(
                f"Refine with peer insights: {task}", 
                collaborative_context
            )
            collaboration_results.append({
                "hierarchy_id": hierarchy_id,
                "initial_analysis": initial_analyses[hierarchy_id],
                "refined_result": refined_result
            })
        
        # Phase 4: Final synthesis
        final_synthesis = self._synthesize_collaborative_results(collaboration_results)
        
        return {
            "pattern": "collaborative",
            "original_task": task,
            "collaboration_phases": 4,
            "collaboration_results": collaboration_results,
            "messages_exchanged": len(messages),
            "final_synthesis": final_synthesis
        }
    
    def _execute_competitive(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute competitive pattern: agents compete for best solution."""
        competitive_results = []
        
        # All agents work on the same task independently
        for hierarchy_id, hierarchy in self.hierarchies.items():
            result = hierarchy.coordinate_task(task, context)
            competitive_results.append({
                "hierarchy_id": hierarchy_id,
                "result": result,
                "confidence": result.get("final_result", {}).get("confidence", 0.5)
            })
        
        for swarm_id, swarm in self.swarms.items():
            swarm_tasks = [SwarmTask(f"competitive_{swarm_id}", task)]
            result = swarm.execute_parallel_tasks(swarm_tasks)
            # Extract confidence from swarm results
            avg_confidence = self._calculate_swarm_confidence(result)
            competitive_results.append({
                "swarm_id": swarm_id,
                "result": result,
                "confidence": avg_confidence
            })
        
        # Select winner based on confidence
        winner = max(competitive_results, key=lambda x: x["confidence"])
        
        return {
            "pattern": "competitive",
            "original_task": task,
            "competitors": len(competitive_results),
            "competitive_results": competitive_results,
            "winner": winner,
            "winning_confidence": winner["confidence"]
        }
    
    def _generate_collaboration_messages(self, analyses: Dict[str, Any]) -> List[AgentMessage]:
        """Generate messages for agent collaboration."""
        messages = []
        
        for sender_id, analysis in analyses.items():
            for receiver_id in analyses.keys():
                if sender_id != receiver_id:
                    message = AgentMessage(
                        sender_id=sender_id,
                        receiver_id=receiver_id,
                        message_type="analysis_sharing",
                        content={
                            "key_insights": analysis.get("final_result", {}).get("synthesized_response", ""),
                            "confidence": analysis.get("final_result", {}).get("confidence", 0.5)
                        },
                        timestamp=1234567890.0,
                        requires_response=False
                    )
                    messages.append(message)
        
        return messages
    
    def _aggregate_broadcast_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate results from broadcast pattern."""
        all_responses = []
        total_confidence = 0
        
        for result in results.values():
            if "final_result" in result:
                response = result["final_result"].get("synthesized_response", "")
                confidence = result["final_result"].get("confidence", 0.5)
            else:
                # Handle swarm results
                response = f"Swarm result with {result.get('task_count', 0)} tasks"
                confidence = result.get("execution_stats", {}).get("success_rate", 0.5)
            
            all_responses.append(response)
            total_confidence += confidence
        
        return {
            "aggregated_responses": all_responses,
            "average_confidence": total_confidence / max(len(results), 1),
            "consensus_strength": len(results)
        }
    
    def _synthesize_collaborative_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Synthesize results from collaborative pattern."""
        refined_insights = []
        
        for result in results:
            refined_result = result.get("refined_result", {})
            if "final_result" in refined_result:
                insight = refined_result["final_result"].get("synthesized_response", "")
                refined_insights.append(insight)
        
        return {
            "collaborative_insights": refined_insights,
            "synthesis_quality": len(refined_insights) / max(len(results), 1),
            "collaboration_effectiveness": 0.85  # Placeholder metric
        }
    
    def _calculate_swarm_confidence(self, swarm_result: Dict[str, Any]) -> float:
        """Calculate average confidence from swarm results."""
        total_confidence = 0
        count = 0
        
        for agent_results in swarm_result.get("agent_results", {}).values():
            for result in agent_results.get("results", []):
                if "confidence" in result:
                    total_confidence += result["confidence"]
                    count += 1
        
        return total_confidence / max(count, 1)
    
    def get_orchestration_stats(self) -> Dict[str, Any]:
        """Get orchestration statistics."""
        return {
            "orchestrator_id": self.orchestrator_id,
            "hierarchies_count": len(self.hierarchies),
            "swarms_count": len(self.swarms),
            "messages_queued": len(self.message_queue),
            "total_agents": sum(len(h.specialists) + 1 for h in self.hierarchies.values()) + 
                           sum(len(s.agents) for s in self.swarms.values())
        }
