"""Per-agent learning persistence and context injection."""
from __future__ import annotations

from typing import Any

from backend.memory.neo4j_memory import Neo4jMemory


class AgentMemory:
    """Per-agent memory layer on top of Neo4jMemory.

    Stores and retrieves agent-specific learnings, preferences,
    and performance data for context injection into agent prompts.
    """

    def __init__(self, memory: Neo4jMemory, agent_name: str):
        self.memory = memory
        self.agent_name = agent_name

    async def store(self, category: str, content: str, confidence: float = 0.8):
        """Store an agent-specific learning."""
        async with self.memory.driver.session() as session:
            await session.run(
                """
                MERGE (a:Agent {name: $agent_name})
                CREATE (l:Learning {
                    category: $category,
                    content: $content,
                    confidence: $confidence,
                    agent: $agent_name,
                    timestamp: datetime()
                })
                CREATE (a)-[:LEARNED]->(l)
                """,
                agent_name=self.agent_name,
                category=category,
                content=content,
                confidence=confidence,
            )

    async def recall(self, category: str | None = None, limit: int = 10) -> list[dict[str, Any]]:
        """Recall agent-specific learnings."""
        async with self.memory.driver.session() as session:
            if category:
                result = await session.run(
                    """
                    MATCH (a:Agent {name: $agent_name})-[:LEARNED]->(l:Learning {category: $category})
                    RETURN l.category as category, l.content as content,
                           l.confidence as confidence, l.timestamp as timestamp
                    ORDER BY l.confidence DESC, l.timestamp DESC
                    LIMIT $limit
                    """,
                    agent_name=self.agent_name, category=category, limit=limit,
                )
            else:
                result = await session.run(
                    """
                    MATCH (a:Agent {name: $agent_name})-[:LEARNED]->(l:Learning)
                    RETURN l.category as category, l.content as content,
                           l.confidence as confidence, l.timestamp as timestamp
                    ORDER BY l.confidence DESC, l.timestamp DESC
                    LIMIT $limit
                    """,
                    agent_name=self.agent_name, limit=limit,
                )

            learnings = []
            async for record in result:
                learnings.append({
                    "category": record["category"],
                    "content": record["content"],
                    "confidence": record["confidence"],
                    "timestamp": str(record["timestamp"]) if record["timestamp"] else None,
                })
            return learnings

    async def get_context_prompt(self, max_items: int = 5) -> str:
        """Generate a context injection string for the agent's prompt.

        Returns relevant past learnings formatted for prompt injection.
        """
        learnings = await self.recall(limit=max_items)
        if not learnings:
            return ""

        lines = [f"\n--- Past Learnings ({self.agent_name}) ---"]
        for l in learnings:
            conf = f"[{l['confidence']:.0%}]" if l.get("confidence") else ""
            lines.append(f"- {conf} [{l['category']}] {l['content']}")
        lines.append("--- End Learnings ---\n")
        return "\n".join(lines)


async def get_agent_memories(memory: Neo4jMemory) -> dict[str, AgentMemory]:
    """Create AgentMemory instances for all known agents."""
    agent_names = [
        "Architect", "Coder", "Critic", "Researcher",
        "Tester", "Optimizer", "MemoryCurator", "Evolutor",
    ]
    return {name: AgentMemory(memory, name) for name in agent_names}
