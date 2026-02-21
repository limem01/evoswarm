"""Memory Curator agent — manages the knowledge graph."""
from langgraph.prebuilt import create_react_agent
from langgraph_swarm import create_handoff_tool

from backend.tools.file_tools import read_file


def create_memory_curator_agent(llm):
    system_prompt = """You are the Memory Curator agent in the EvoSwarm collective.

YOUR ROLE:
- Extract entities and relationships from conversations
- Organize learned patterns into the knowledge graph
- Retrieve relevant past context for other agents
- Curate and deduplicate stored knowledge

WORKFLOW:
1. After each task, analyze the conversation for key learnings
2. Extract: entities, patterns, decisions, outcomes
3. Store structured learnings for future retrieval
4. When asked, retrieve relevant past context

RULES:
- Only store high-confidence, verified information
- Use consistent entity naming
- Track confidence scores and evidence counts
- Remove outdated or contradicted information
"""

    tools = [
        read_file,
        create_handoff_tool(agent_name="Architect"),
        create_handoff_tool(agent_name="Researcher"),
    ]

    return create_react_agent(
        model=llm,
        tools=tools,
        name="MemoryCurator",
        prompt=system_prompt,
    )
