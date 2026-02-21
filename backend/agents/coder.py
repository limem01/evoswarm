"""Coder Agent - Implementation and code generation."""
from langgraph.prebuilt import create_react_agent
from langgraph_swarm import create_handoff_tool

from backend.tools.file_tools import read_file, write_file, list_directory
from backend.tools.git_tools import git_init, git_commit
from backend.tools.sandbox import run_code


CODER_PROMPT = """You are the Coder agent in the EvoSwarm collective.

Your responsibilities:
1. Write clean, efficient, well-documented code
2. Implement features according to specifications
3. Fix bugs and refactor existing code
4. Follow best practices and coding standards

When implementing:
1. Read existing code to understand context
2. Write modular, testable code
3. Add appropriate comments and docstrings
4. Commit changes with descriptive messages

Hand off to:
- Critic: For code review after implementation
- Tester: For testing the implementation
- Architect: For clarification on requirements

Always write production-quality code."""


def create_coder_agent(llm):
    """Create the Coder agent with coding tools and handoffs."""
    tools = [
        read_file,
        write_file,
        list_directory,
        git_init,
        git_commit,
        run_code,
        create_handoff_tool(
            agent_name="Critic",
            description="Hand off code for review to the Critic agent",
        ),
        create_handoff_tool(
            agent_name="Tester",
            description="Hand off code for testing to the Tester agent",
        ),
        create_handoff_tool(
            agent_name="Architect",
            description="Hand off to Architect for clarification or design changes",
        ),
    ]
    
    return create_react_agent(
        llm,
        tools=tools,
        name="Coder",
        prompt=CODER_PROMPT,
    )
