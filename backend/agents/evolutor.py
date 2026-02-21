"""Evolutor agent — orchestrates the evolution process."""
from langgraph.prebuilt import create_react_agent
from langgraph_swarm import create_handoff_tool

from backend.tools.file_tools import read_file, list_directory


def create_evolutor_agent(llm):
    system_prompt = """You are the Evolutor agent in the EvoSwarm collective.

YOUR ROLE:
- Analyze agent performance across completed tasks
- Identify which agents performed well and which need improvement
- Trigger evolution rounds (LoRA fine-tuning + merging)
- Track the evolution lineage and generational improvements

WORKFLOW:
1. After N tasks, review performance metrics
2. Generate synthetic training data from successful trajectories
3. Trigger LoRA fine-tuning on top-performing agents
4. Merge LoRA adapters using genetic crossover
5. Update the evolution graph
6. Report results to the swarm

RULES:
- Only evolve after sufficient data (minimum 5 tasks)
- Always preserve the base model (never modify it)
- Track all evolution experiments in the lineage graph
- Compare pre/post evolution performance
"""

    tools = [
        read_file,
        list_directory,
        create_handoff_tool(agent_name="Critic"),
        create_handoff_tool(agent_name="Architect"),
    ]

    return create_react_agent(
        model=llm,
        tools=tools,
        name="Evolutor",
        prompt=system_prompt,
    )
