"""Researcher agent — gathers information and context."""
from langgraph.prebuilt import create_react_agent
from langgraph_swarm import create_handoff_tool

from backend.tools.file_tools import read_file, list_directory


def create_researcher_agent(llm):
    system_prompt = """You are the Researcher agent in the EvoSwarm collective.

YOUR ROLE:
- Gather information needed by other agents
- Read and analyze existing codebases
- Summarize documentation and patterns
- Provide context for architectural decisions

WORKFLOW:
1. Receive a research request from another agent
2. Read relevant files and documentation
3. Synthesize findings into a clear summary
4. Hand off results to the requesting agent (usually Architect)

RULES:
- Be thorough but concise
- Cite specific file paths and line numbers
- Identify patterns and anti-patterns
- Flag any concerns or risks
"""

    tools = [
        read_file,
        list_directory,
        create_handoff_tool(agent_name="Architect"),
        create_handoff_tool(agent_name="Coder"),
    ]

    return create_react_agent(
        model=llm,
        tools=tools,
        name="Researcher",
        prompt=system_prompt,
    )
