"""
EvoSwarm configuration: state schema, agent wiring, swarm compilation.

Supports multiple LLM providers:
- ollama (local, free)
- openai (GPT-5)
- anthropic (Claude)
- google (Gemini)
- xai (Grok)

Set LLM_PROVIDER in .env to switch between them.
"""
import os
from typing import Annotated, TypedDict

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
    """Create the LLM instance based on configured provider."""
    provider = os.getenv("LLM_PROVIDER", "ollama").lower()
    
    if provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-5"),
            api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0.7,
        )
    
    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"),
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            temperature=0.7,
        )
    
    elif provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=os.getenv("GOOGLE_MODEL", "gemini-2.0-flash"),
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.7,
        )
    
    elif provider == "xai":
        from langchain_xai import ChatXAI
        return ChatXAI(
            model=os.getenv("XAI_MODEL", "grok-4.2"),
            api_key=os.getenv("XAI_API_KEY"),
            temperature=0.7,
        )
    
    else:  # Default to Ollama (local)
        from langchain_ollama import ChatOllama
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
