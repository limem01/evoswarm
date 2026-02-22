"""Evolution orchestration tools for the Evolutor agent."""
from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from langchain_core.tools import tool

if TYPE_CHECKING:
    from backend.event_bus import EventBus
    from backend.memory.neo4j_memory import Neo4jMemory

_memory: Neo4jMemory | None = None
_event_bus: EventBus | None = None
_evolution_status: dict = {"running": False, "last_result": None}


def set_evolution_deps(memory: Neo4jMemory, event_bus: EventBus):
    """Inject dependencies (called at startup)."""
    global _memory, _event_bus
    _memory = memory
    _event_bus = event_bus


@tool
async def trigger_evolution(generations: int = 1) -> str:
    """Trigger an evolution round to train and merge agent LoRA adapters.

    Args:
        generations: Number of evolution generations to run

    Returns:
        Summary of the evolution results
    """
    global _evolution_status
    if _memory is None or _event_bus is None:
        return "Error: Evolution dependencies not initialized."
    if _evolution_status["running"]:
        return "Evolution is already running. Check status with get_evolution_status."

    from backend.evolution.evaluator import run_evolution_round

    _evolution_status["running"] = True
    results = []
    try:
        for i in range(generations):
            result = await run_evolution_round(_memory, _event_bus)
            results.append(result)
        _evolution_status["last_result"] = results
        return f"Evolution complete. {len(results)} generation(s) processed. Results: {results}"
    except Exception as e:
        return f"Evolution failed: {e}"
    finally:
        _evolution_status["running"] = False


@tool
async def get_evolution_status() -> str:
    """Get the current evolution status and last results.

    Returns:
        Current evolution status
    """
    if _evolution_status["running"]:
        return "Evolution is currently running..."
    if _evolution_status["last_result"]:
        return f"Last evolution result: {_evolution_status['last_result']}"
    return "No evolution has been run yet."


@tool
async def get_evolution_lineage() -> str:
    """Get the evolution lineage graph from Neo4j.

    Returns:
        Formatted lineage showing parent-child model relationships
    """
    if _memory is None:
        return "Error: Memory not initialized."
    graph = await _memory.get_evolution_graph()
    nodes = graph.get("nodes", [])
    links = graph.get("links", [])
    if not nodes:
        return "No evolution lineage data yet."
    lines = [f"Lineage: {len(nodes)} model versions, {len(links)} evolution links"]
    for link in links:
        lines.append(f"  {link['source']} -> {link['target']}")
    return "\n".join(lines)
