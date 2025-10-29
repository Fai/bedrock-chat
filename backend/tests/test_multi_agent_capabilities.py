"""
Tests for multi-agent capabilities.

Tests hierarchical agents, swarm coordination, and orchestration patterns.
"""

import pytest
from unittest.mock import Mock, patch

from app.agents.multi_agent.hierarchy import HierarchicalAgent, AgentHierarchy, AgentRole
from app.agents.multi_agent.swarm import AgentSwarm, SwarmTask, SwarmOrchestrator
from app.agents.multi_agent.orchestrator import MultiAgentOrchestrator, OrchestrationPattern
from app.repositories.models.custom_bot import BotModel, GenerationParamsModel, AgentModel, AgentToolModel


class TestHierarchicalAgents:
    """Test suite for hierarchical agent system."""

    @pytest.fixture
    def mock_coordinator_bot(self):
        """Create mock coordinator bot."""
        return BotModel(
            id="coordinator-bot",
            title="Coordinator",
            instruction="You coordinate tasks across specialists",
            description="Coordinator bot",
            generation_params=GenerationParamsModel(temperature=0.7, top_p=0.9, max_tokens=1024),
            agent=AgentModel(tools=[]),
            bedrock_knowledge_base=None,
            is_pinned=False,
            is_public=False,
            owned=True,
            available=True,
            sync_status="SUCCEEDED",
            has_knowledge=False,
            display_retrieved_chunks=False,
            create_time=1234567890.0,
            last_used_time=1234567890.0,
        )

    @pytest.fixture
    def mock_specialist_bot(self):
        """Create mock specialist bot."""
        return BotModel(
            id="specialist-bot",
            title="Knowledge Specialist",
            instruction="You are a knowledge specialist",
            description="Specialist bot",
            generation_params=GenerationParamsModel(temperature=0.7, top_p=0.9, max_tokens=1024),
            agent=AgentModel(tools=[
                AgentToolModel(name="knowledge", enabled=True)
            ]),
            bedrock_knowledge_base=Mock(),
            is_pinned=False,
            is_public=False,
            owned=True,
            available=True,
            sync_status="SUCCEEDED",
            has_knowledge=True,
            display_retrieved_chunks=True,
            create_time=1234567890.0,
            last_used_time=1234567890.0,
        )

    def test_hierarchical_agent_initialization(self, mock_coordinator_bot):
        """Test hierarchical agent initialization."""
        agent = HierarchicalAgent("coord-1", AgentRole.COORDINATOR, mock_coordinator_bot, "claude-3-5-sonnet")
        
        assert agent.agent_id == "coord-1"
        assert agent.role == AgentRole.COORDINATOR
        assert agent.capabilities["can_delegate"] is True
        assert agent.capabilities["max_specialists"] == 5

    def test_specialist_agent_capabilities(self, mock_specialist_bot):
        """Test specialist agent capabilities detection."""
        agent = HierarchicalAgent("spec-1", AgentRole.SPECIALIST, mock_specialist_bot, "claude-3-5-sonnet")
        
        assert agent.role == AgentRole.SPECIALIST
        assert agent.capabilities["specialization"] == "knowledge_specialist"
        assert agent.capabilities["can_delegate"] is False

    def test_agent_hierarchy_creation(self, mock_coordinator_bot):
        """Test agent hierarchy creation."""
        hierarchy = AgentHierarchy(mock_coordinator_bot, "claude-3-5-sonnet")
        
        assert hierarchy.coordinator.role == AgentRole.COORDINATOR
        assert len(hierarchy.specialists) == 0

    def test_add_specialist_to_hierarchy(self, mock_coordinator_bot, mock_specialist_bot):
        """Test adding specialist to hierarchy."""
        hierarchy = AgentHierarchy(mock_coordinator_bot, "claude-3-5-sonnet")
        
        specialist = hierarchy.add_specialist("spec-1", mock_specialist_bot, "claude-3-5-sonnet")
        
        assert "spec-1" in hierarchy.specialists
        assert specialist.capabilities["specialization"] == "knowledge_specialist"

    def test_coordinate_task(self, mock_coordinator_bot, mock_specialist_bot):
        """Test task coordination."""
        hierarchy = AgentHierarchy(mock_coordinator_bot, "claude-3-5-sonnet")
        hierarchy.add_specialist("spec-1", mock_specialist_bot, "claude-3-5-sonnet")
        
        result = hierarchy.coordinate_task("What is machine learning?")
        
        assert "task" in result
        assert "delegation_plan" in result
        assert "final_result" in result
        assert result["task"] == "What is machine learning?"


class TestAgentSwarm:
    """Test suite for agent swarm coordination."""

    @pytest.fixture
    def mock_agents(self, mock_coordinator_bot):
        """Create mock agents for swarm."""
        agents = []
        for i in range(3):
            agent = HierarchicalAgent(f"agent-{i}", AgentRole.SPECIALIST, mock_coordinator_bot, "claude-3-5-sonnet")
            agents.append(agent)
        return agents

    def test_swarm_initialization(self):
        """Test swarm initialization."""
        swarm = AgentSwarm("test-swarm", max_workers=3)
        
        assert swarm.swarm_id == "test-swarm"
        assert swarm.max_workers == 3
        assert len(swarm.agents) == 0

    def test_add_agent_to_swarm(self, mock_agents):
        """Test adding agents to swarm."""
        swarm = AgentSwarm("test-swarm")
        
        for agent in mock_agents:
            swarm.add_agent(agent)
        
        assert len(swarm.agents) == 3
        assert "agent-0" in swarm.agents

    def test_swarm_task_creation(self):
        """Test swarm task creation."""
        task = SwarmTask("task-1", "Test task", priority=2, requires_consensus=True)
        
        assert task.task_id == "task-1"
        assert task.description == "Test task"
        assert task.priority == 2
        assert task.requires_consensus is True

    def test_execute_parallel_tasks(self, mock_agents):
        """Test parallel task execution."""
        swarm = AgentSwarm("test-swarm")
        for agent in mock_agents:
            swarm.add_agent(agent)
        
        tasks = [
            SwarmTask("task-1", "Task 1"),
            SwarmTask("task-2", "Task 2"),
            SwarmTask("task-3", "Task 3", requires_consensus=True)
        ]
        
        result = swarm.execute_parallel_tasks(tasks)
        
        assert result["swarm_id"] == "test-swarm"
        assert result["task_count"] == 3
        assert "agent_results" in result
        assert "execution_stats" in result

    def test_swarm_orchestrator(self):
        """Test swarm orchestrator."""
        orchestrator = SwarmOrchestrator()
        
        swarm1 = orchestrator.create_swarm("swarm-1")
        swarm2 = orchestrator.create_swarm("swarm-2")
        
        assert len(orchestrator.swarms) == 2
        assert "swarm-1" in orchestrator.swarms


class TestMultiAgentOrchestrator:
    """Test suite for multi-agent orchestrator."""

    @pytest.fixture
    def orchestrator_with_components(self, mock_coordinator_bot, mock_specialist_bot):
        """Create orchestrator with hierarchy and swarm."""
        orchestrator = MultiAgentOrchestrator("test-orchestrator")
        
        # Add hierarchy
        hierarchy = AgentHierarchy(mock_coordinator_bot, "claude-3-5-sonnet")
        hierarchy.add_specialist("spec-1", mock_specialist_bot, "claude-3-5-sonnet")
        orchestrator.add_hierarchy("hierarchy-1", hierarchy)
        
        # Add swarm
        swarm = AgentSwarm("swarm-1")
        agent = HierarchicalAgent("swarm-agent-1", AgentRole.SPECIALIST, mock_specialist_bot, "claude-3-5-sonnet")
        swarm.add_agent(agent)
        orchestrator.add_swarm("swarm-1", swarm)
        
        return orchestrator

    def test_orchestrator_initialization(self):
        """Test orchestrator initialization."""
        orchestrator = MultiAgentOrchestrator("test-orchestrator")
        
        assert orchestrator.orchestrator_id == "test-orchestrator"
        assert len(orchestrator.hierarchies) == 0
        assert len(orchestrator.swarms) == 0

    def test_pipeline_pattern(self, orchestrator_with_components):
        """Test pipeline orchestration pattern."""
        result = orchestrator_with_components.execute_pattern(
            OrchestrationPattern.PIPELINE,
            "Analyze market trends"
        )
        
        assert result["pattern"] == "pipeline"
        assert "pipeline_stages" in result
        assert "final_output" in result

    def test_broadcast_pattern(self, orchestrator_with_components):
        """Test broadcast orchestration pattern."""
        result = orchestrator_with_components.execute_pattern(
            OrchestrationPattern.BROADCAST,
            "Generate creative ideas"
        )
        
        assert result["pattern"] == "broadcast"
        assert "broadcast_targets" in result
        assert "aggregated_result" in result

    def test_collaborative_pattern(self, orchestrator_with_components):
        """Test collaborative orchestration pattern."""
        result = orchestrator_with_components.execute_pattern(
            OrchestrationPattern.COLLABORATIVE,
            "Solve complex problem"
        )
        
        assert result["pattern"] == "collaborative"
        assert result["collaboration_phases"] == 4
        assert "final_synthesis" in result

    def test_competitive_pattern(self, orchestrator_with_components):
        """Test competitive orchestration pattern."""
        result = orchestrator_with_components.execute_pattern(
            OrchestrationPattern.COMPETITIVE,
            "Find best solution"
        )
        
        assert result["pattern"] == "competitive"
        assert "winner" in result
        assert "winning_confidence" in result

    def test_orchestration_stats(self, orchestrator_with_components):
        """Test orchestration statistics."""
        stats = orchestrator_with_components.get_orchestration_stats()
        
        assert stats["orchestrator_id"] == "test-orchestrator"
        assert stats["hierarchies_count"] == 1
        assert stats["swarms_count"] == 1
        assert stats["total_agents"] > 0

    def test_invalid_pattern(self, orchestrator_with_components):
        """Test invalid orchestration pattern."""
        with pytest.raises(ValueError):
            orchestrator_with_components.execute_pattern("invalid_pattern", "test task")


class TestIntegrationScenarios:
    """Integration tests for multi-agent scenarios."""

    def test_complex_multi_agent_scenario(self, mock_coordinator_bot, mock_specialist_bot):
        """Test complex multi-agent scenario with multiple patterns."""
        # Create orchestrator
        orchestrator = MultiAgentOrchestrator("complex-orchestrator")
        
        # Create multiple hierarchies
        for i in range(2):
            hierarchy = AgentHierarchy(mock_coordinator_bot, "claude-3-5-sonnet")
            hierarchy.add_specialist(f"spec-{i}", mock_specialist_bot, "claude-3-5-sonnet")
            orchestrator.add_hierarchy(f"hierarchy-{i}", hierarchy)
        
        # Create swarm
        swarm = AgentSwarm("analysis-swarm")
        for i in range(3):
            agent = HierarchicalAgent(f"swarm-agent-{i}", AgentRole.SPECIALIST, mock_specialist_bot, "claude-3-5-sonnet")
            swarm.add_agent(agent)
        orchestrator.add_swarm("analysis-swarm", swarm)
        
        # Execute collaborative pattern
        result = orchestrator.execute_pattern(
            OrchestrationPattern.COLLABORATIVE,
            "Develop comprehensive business strategy"
        )
        
        assert result["pattern"] == "collaborative"
        assert len(result["collaboration_results"]) == 2  # Two hierarchies
        assert result["messages_exchanged"] > 0

    def test_performance_metrics(self, orchestrator_with_components):
        """Test performance metrics collection."""
        # Execute multiple patterns
        patterns = [
            OrchestrationPattern.PIPELINE,
            OrchestrationPattern.BROADCAST,
            OrchestrationPattern.COLLABORATIVE
        ]
        
        results = []
        for pattern in patterns:
            result = orchestrator_with_components.execute_pattern(pattern, f"Task for {pattern.value}")
            results.append(result)
        
        # Verify all patterns executed successfully
        assert len(results) == 3
        assert all("pattern" in result for result in results)
        
        # Check orchestration stats
        stats = orchestrator_with_components.get_orchestration_stats()
        assert stats["total_agents"] >= 2  # At least coordinator + specialist
