"""EvoSwarm Agent Creators."""
from backend.agents.architect import create_architect_agent
from backend.agents.coder import create_coder_agent
from backend.agents.critic import create_critic_agent
from backend.agents.researcher import create_researcher_agent
from backend.agents.tester import create_tester_agent
from backend.agents.optimizer import create_optimizer_agent
from backend.agents.memory_curator import create_memory_curator_agent
from backend.agents.evolutor import create_evolutor_agent

__all__ = [
    "create_architect_agent",
    "create_coder_agent",
    "create_critic_agent",
    "create_researcher_agent",
    "create_tester_agent",
    "create_optimizer_agent",
    "create_memory_curator_agent",
    "create_evolutor_agent",
]
