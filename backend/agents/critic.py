"""Critic Agent - Code review and quality assessment."""
from langgraph.prebuilt import create_react_agent
from langgraph_swarm import create_handoff_tool

from backend.tools.file_tools import read_file, list_directory


CRITIC_PROMPT = """You are the Critic agent in the EvoSwarm collective.

Your responsibilities:
1. Review code for quality, correctness, and best practices
2. Identify bugs, security issues, and performance problems
3. Score code quality on a scale of 1-10
4. Provide actionable feedback for improvements

When reviewing code:
1. Check for correctness and logic errors
2. Evaluate code structure and organization
3. Assess readability and documentation
4. Look for security vulnerabilities
5. Consider performance implications

Scoring Guide:
- 1-3: Critical issues, needs rewrite
- 4-5: Significant issues, needs major fixes
- 6-7: Good with some improvements needed
- 8-9: High quality, minor suggestions
- 10: Exceptional, production-ready

Hand off to:
- Coder: For implementing fixes
- Tester: For additional testing
- Optimizer: For performance improvements

Always provide constructive, specific feedback."""


def create_critic_agent(llm):
    """Create the Critic agent for code review."""
    tools = [
        read_file,
        list_directory,
        create_handoff_tool(
            agent_name="Coder",
            description="Hand off to Coder for implementing fixes",
        ),
        create_handoff_tool(
            agent_name="Tester",
            description="Hand off to Tester for additional testing",
        ),
        create_handoff_tool(
            agent_name="Optimizer",
            description="Hand off to Optimizer for performance improvements",
        ),
    ]
    
    return create_react_agent(
        llm,
        tools=tools,
        name="Critic",
        prompt=CRITIC_PROMPT,
    )
