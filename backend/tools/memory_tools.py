"""Memory tools wrapping Neo4j operations for the Memory Curator agent."""
from __future__ import annotations

from typing import TYPE_CHECKING

from langchain_core.tools import tool

if TYPE_CHECKING:
    from backend.memory.neo4j_memory import Neo4jMemory

_memory: Neo4jMemory | None = None


def set_memory(memory: Neo4jMemory):
    """Inject the Neo4jMemory instance (called at startup)."""
    global _memory
    _memory = memory


def _get_memory() -> Neo4jMemory:
    if _memory is None:
        raise RuntimeError("Memory not initialized - call set_memory() first")
    return _memory


@tool
async def store_learning(category: str, content: str, source_task_id: str = "") -> str:
    """Store a learning/insight into the knowledge graph.

    Args:
        category: Category for the learning (e.g. 'pattern', 'decision', 'lesson')
        content: The learning content to store
        source_task_id: Optional task ID that produced this learning

    Returns:
        Confirmation message
    """
    mem = _get_memory()
    await mem.store_learning(category, content, source_task_id or None)
    return f"Stored learning in category '{category}': {content[:100]}..."


@tool
async def get_learnings(category: str = "", limit: int = 20) -> str:
    """Retrieve learnings from the knowledge graph.

    Args:
        category: Optional category filter
        limit: Maximum number of learnings to return

    Returns:
        Formatted list of learnings
    """
    mem = _get_memory()
    learnings = await mem.get_learnings(category=category or None, limit=limit)
    if not learnings:
        return "No learnings found."
    lines = []
    for i, l in enumerate(learnings, 1):
        lines.append(f"{i}. [{l['category']}] {l['content']}")
    return "\n".join(lines)


@tool
async def search_tasks(query: str = "", limit: int = 20) -> str:
    """Search recent tasks in the knowledge graph.

    Args:
        query: Optional search text (filters task descriptions)
        limit: Maximum number of tasks to return

    Returns:
        Formatted list of tasks
    """
    mem = _get_memory()
    tasks = await mem.get_recent_tasks(limit=limit)
    if query:
        tasks = [t for t in tasks if query.lower() in (t.get("task", "") + t.get("result", "")).lower()]
    if not tasks:
        return "No tasks found."
    lines = []
    for t in tasks:
        lines.append(f"[{t['id']}] {t['task'][:120]}")
    return "\n".join(lines)
