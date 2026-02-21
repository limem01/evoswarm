"""Architect Agent - System design and task decomposition."""
from langgraph.prebuilt import create_react_agent
from langgraph_swarm import create_handoff_tool

from backend.tools.file_tools import read_file, write_file, list_directory


ARCHITECT_PROMPT = """You are the Architect agent in the EvoSwarm collective.

Your responsibilities:
1. Analyze complex tasks and break them down into manageable subtasks
2. Design system architecture and component structures
3. Create implementation plans with clear specifications
4. Coordinate work between other agents

When you receive a task:
1. Understand the requirements fully
2. Design the solution architecture
3. Break down into specific implementation tasks
4. Hand off to appropriate agents:
   - Coder: For implementation tasks
   - Researcher: For gathering information
   - Critic: For reviewing designs

Always think systematically and create clear, actionable plans."""


def create_architect_agent(llm):
    """Create the Architect agent with handoff capabilities."""
    tools = [
        read_file,
        write_file,
        list_directory,
        create_handoff_tool(
            agent_name="Coder",
            description="Hand off implementation tasks to the Coder agent",
        ),
        create_handoff_tool(
            agent_name="Researcher",
            description="Hand off research tasks to the Researcher agent",
        ),
        create_handoff_tool(
            agent_name="Critic",
            description="Hand off design review to the Critic agent",
        ),
    ]
    
    return create_react_agent(
        llm,
        tools=tools,
        name="Architect",
        prompt=ARCHITECT_PROMPT,
    )
