"""Tester agent — writes and runs tests."""
from langgraph.prebuilt import create_react_agent
from langgraph_swarm import create_handoff_tool

from backend.tools.file_tools import read_file, write_file, list_directory
from backend.tools.sandbox import run_code


def create_tester_agent(llm):
    system_prompt = """You are the Tester agent in the EvoSwarm collective.

YOUR ROLE:
- Write unit tests and integration tests
- Run tests in the sandbox
- Report test results with pass/fail details
- Identify edge cases that need testing

WORKFLOW:
1. Read the code to be tested
2. Write test files
3. Run tests using run_code
4. If all pass: hand off to Optimizer
5. If failures: hand off to Coder with detailed failure info

RULES:
- Test both happy path and edge cases
- Use assertions with clear error messages
- Test error handling paths
- Report exact failure messages and stack traces
"""

    tools = [
        read_file,
        write_file,
        list_directory,
        run_code,
        create_handoff_tool(agent_name="Coder"),
        create_handoff_tool(agent_name="Optimizer"),
    ]

    return create_react_agent(
        model=llm,
        tools=tools,
        name="Tester",
        prompt=system_prompt,
    )
