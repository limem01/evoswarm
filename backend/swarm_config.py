"""
EvoSwarm configuration: state schema, agent wiring, swarm compilation.

Supports multiple LLM providers with both API key and OAuth authentication:
- ollama (local, free)
- openai (GPT-5) - API key or Azure AD OAuth
- anthropic (Claude) - API key
- google (Gemini) - API key or OAuth2
- xai (Grok 4.2) - API key or OAuth via X account

Set LLM_PROVIDER and *_AUTH_METHOD in .env to configure.
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
from backend.auth import get_credentials


class EvoSwarmState(TypedDict):
    messages: Annotated[list, add_messages]


def get_llm():
    """Create the LLM instance based on configured provider and auth method."""
    provider = os.getenv("LLM_PROVIDER", "ollama").lower()
    creds = get_credentials(provider)

    if provider == "openai":
        from langchain_openai import ChatOpenAI, AzureChatOpenAI

        if creds.get("api_type") == "azure_ad":
            return AzureChatOpenAI(
                azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-5"),
                azure_endpoint=creds["api_base"],
                api_key=creds["api_key"],
                api_version=creds["api_version"],
                temperature=0.7,
            )
        else:
            return ChatOpenAI(
                model=os.getenv("OPENAI_MODEL", "gpt-5"),
                api_key=creds["api_key"],
                temperature=0.7,
            )

    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"),
            api_key=creds["api_key"],
            temperature=0.7,
        )

    elif provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI

        if "credentials" in creds:
            return ChatGoogleGenerativeAI(
                model=os.getenv("GOOGLE_MODEL", "gemini-2.0-flash"),
                credentials=creds["credentials"],
                temperature=0.7,
            )
        else:
            return ChatGoogleGenerativeAI(
                model=os.getenv("GOOGLE_MODEL", "gemini-2.0-flash"),
                google_api_key=creds["google_api_key"],
                temperature=0.7,
            )

    elif provider == "xai":
        from langchain_xai import ChatXAI
        return ChatXAI(
            model=os.getenv("XAI_MODEL", "grok-4.2"),
            api_key=creds["api_key"],
            temperature=0.7,
        )

    else:  # Default to Ollama (local)
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model=os.getenv("OLLAMA_MODEL", "llama3.1:8b-instruct-q4_K_M"),
            temperature=0.7,
            num_ctx=8192,
        )


def _build_agent_tools(approval_manager=None):
    """Build per-agent extra_tools based on role.

    Returns a dict mapping agent creator function to extra tools list.
    """
    extra = {}

    if not approval_manager:
        return extra

    # Import PC control tools (they may not be available if deps missing)
    pc_tools = {}
    try:
        from backend.tools.shell_tools import execute_shell, execute_shell_background, get_process_output
        pc_tools["shell"] = [execute_shell, execute_shell_background, get_process_output]
    except ImportError:
        pc_tools["shell"] = []

    try:
        from backend.tools.browser_tools import (
            browser_navigate, browser_click, browser_type,
            browser_screenshot, browser_extract_text, browser_get_links,
        )
        pc_tools["browser"] = [
            browser_navigate, browser_click, browser_type,
            browser_screenshot, browser_extract_text, browser_get_links,
        ]
    except ImportError:
        pc_tools["browser"] = []

    try:
        from backend.tools.screen_tools import take_screenshot
        pc_tools["screen"] = [take_screenshot]
    except ImportError:
        pc_tools["screen"] = []

    try:
        from backend.tools.input_tools import type_text, click_position, press_key
        pc_tools["input"] = [type_text, click_position, press_key]
    except ImportError:
        pc_tools["input"] = []

    try:
        from backend.tools.process_tools import list_processes, kill_process
        pc_tools["process"] = [list_processes, kill_process]
    except ImportError:
        pc_tools["process"] = []

    try:
        from backend.tools.system_tools import system_info
        pc_tools["system"] = [system_info]
    except ImportError:
        pc_tools["system"] = []

    try:
        from backend.tools.clipboard_tools import read_clipboard, write_clipboard
        pc_tools["clipboard"] = [read_clipboard, write_clipboard]
    except ImportError:
        pc_tools["clipboard"] = []

    try:
        from backend.tools.app_tools import launch_app
        pc_tools["app"] = [launch_app]
    except ImportError:
        pc_tools["app"] = []

    all_pc = []
    for tools in pc_tools.values():
        all_pc.extend(tools)

    # Coder gets ALL PC tools
    extra["coder"] = list(all_pc)

    # Researcher gets browser tools
    extra["researcher"] = pc_tools.get("browser", []) + pc_tools.get("screen", [])

    # Tester gets shell + process tools
    extra["tester"] = pc_tools.get("shell", []) + pc_tools.get("process", [])

    # Optimizer gets shell + process tools
    extra["optimizer"] = pc_tools.get("shell", []) + pc_tools.get("process", [])

    # Architect gets shell (read-only) + system info
    extra["architect"] = pc_tools.get("shell", []) + pc_tools.get("system", [])

    # Critic gets shell + system info
    extra["critic"] = pc_tools.get("shell", []) + pc_tools.get("system", [])

    return extra


def create_evoswarm(memory=None, approval_manager=None):
    """Build and compile the swarm.

    Args:
        memory: Optional Neo4jMemory instance for memory/evolution tools.
        approval_manager: Optional ApprovalManager for PC control tool approval.
    """
    llm = get_llm()

    # Initialize tool dependencies
    if memory:
        from backend.tools.memory_tools import set_memory
        from backend.tools.evolution_tools import set_evolution_deps
        from backend.event_bus import event_bus
        set_memory(memory)
        set_evolution_deps(memory, event_bus)

    if approval_manager:
        # Set approval manager on all tool modules that need it
        tool_modules = [
            "backend.tools.shell_tools",
            "backend.tools.browser_tools",
            "backend.tools.screen_tools",
            "backend.tools.input_tools",
            "backend.tools.process_tools",
            "backend.tools.system_tools",
            "backend.tools.clipboard_tools",
            "backend.tools.app_tools",
        ]
        for mod_name in tool_modules:
            try:
                import importlib
                mod = importlib.import_module(mod_name)
                if hasattr(mod, "set_approval_manager"):
                    mod.set_approval_manager(approval_manager)
            except ImportError:
                pass

    agent_tools = _build_agent_tools(approval_manager)

    agents = [
        create_architect_agent(llm, extra_tools=agent_tools.get("architect")),
        create_coder_agent(llm, extra_tools=agent_tools.get("coder")),
        create_critic_agent(llm, extra_tools=agent_tools.get("critic")),
        create_researcher_agent(llm, extra_tools=agent_tools.get("researcher")),
        create_tester_agent(llm, extra_tools=agent_tools.get("tester")),
        create_optimizer_agent(llm, extra_tools=agent_tools.get("optimizer")),
        create_memory_curator_agent(llm, extra_tools=agent_tools.get("memory_curator")),
        create_evolutor_agent(llm, extra_tools=agent_tools.get("evolutor")),
    ]

    workflow = create_swarm(
        agents=agents,
        default_active_agent="Architect",
    )

    checkpointer = InMemorySaver()
    return workflow.compile(checkpointer=checkpointer)
