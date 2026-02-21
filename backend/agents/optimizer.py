"""Optimizer agent — improves performance and efficiency."""
from langgraph.prebuilt import create_react_agent
from langgraph_swarm import create_handoff_tool

from backend.tools.file_tools import read_file, write_file, list_directory
from backend.tools.sandbox import run_code


def create_optimizer_agent(llm):
    system_prompt = """You are the Optimizer agent in the EvoSwarm collective.

YOUR ROLE:
- Profile code for performance bottlenecks
- Optimize algorithms and data structures
- Reduce memory usage and improve speed
- Suggest caching strategies and async patterns

WORKFLOW:
1. Read the code to optimize
2. Identify bottlenecks (O(n^2) loops, redundant I/O, etc.)
3. Write optimized version
4. Run benchmarks to verify improvement
5. Hand off to Critic for review

RULES:
- Only optimize after code is correct (don't premature-optimize)
- Measure before and after
- Document what was changed and why
- Don't sacrifice readability for marginal gains
"""

    tools = [
        read_file,
        write_file,
        list_directory,
        run_code,
        create_handoff_tool(agent_name="Critic"),
        create_handoff_tool(agent_name="Coder"),
    ]

    return create_react_agent(
        model=llm,
        tools=tools,
        name="Optimizer",
        prompt=system_prompt,
    )
