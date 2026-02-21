"""
EvoSwarm configuration: state schema, agent wiring, swarm compilation.

IMPORTANT API NOTES (verified Feb 2026):
- langgraph 1.0.7: create_react_agent is in langgraph.prebuilt (deprecated but works)
- langgraph-swarm 0.0.15: create_swarm + create_handoff_tool
- ChatOllama from langchain_ollama 1.0.1
- State uses TypedDict + Annotated[list, add_messages]
- Swarm must be compiled with .compile() before use
- Always pass a checkpointer for multi-turn state persistence
"""
import os
from typing import Annotated, TypedDict

from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import add_messages
from langgraph_swarm import create_swarm

from backend.agents import (
    create_architect_agent,
    create_coder_agent,
    create_critic_agent,
    create_researcher_agent,
    create_tester_agent,
    create_optimizer_agent,
    create_memory_curator_agent,
    create_evolutor_agent,
)


class EvoSwarmState(TypedDict):
    messages: Annotated[list, add_messages]


def get_llm():
    """Create the shared LLM instance."""
    return ChatOllama(
        model=os.getenv("OLLAMA_MODEL", "llama3.1:8b-instruct-q4_K_M"),
        temperature=0.7,
        num_ctx=8192,
    )


def create_evoswarm():
    """Build and compile the swarm."""
    llm = get_llm()

    agents = [
        create_architect_agent(llm),
        create_coder_agent(llm),
        create_critic_agent(llm),
        create_researcher_agent(llm),
        create_tester_agent(llm),
        create_optimizer_agent(llm),
        create_memory_curator_agent(llm),
        create_evolutor_agent(llm),
    ]

    workflow = create_swarm(
        agents=agents,
        default_active_agent="Architect",
    )

    checkpointer = InMemorySaver()
    return workflow.compile(checkpointer=checkpointer)
