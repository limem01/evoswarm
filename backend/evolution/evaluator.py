"""
Evolution orchestrator: ties together data generation, training, merging,
and evaluation into a single evolution round.
"""
import os
import json
from datetime import datetime

from backend.evolution.data_generator import generate_sft_data, save_dataset
from backend.evolution.trainer import train_lora
from backend.evolution.merger import merge_loras, select_parents
from backend.event_bus import EventBus, EventType
from backend.memory.neo4j_memory import Neo4jMemory


# Track evolution state
_generation = 0


async def run_evolution_round(
    memory: Neo4jMemory,
    event_bus: EventBus,
) -> dict:
    """
    Execute one full evolution round:
    1. Gather task logs
    2. Generate synthetic training data
    3. Train LoRA adapters
    4. Merge top performers
    5. Update lineage graph
    6. Broadcast results

    Returns:
        Summary dict with generation info and scores
    """
    global _generation
    _generation += 1
    gen = _generation

    result = {
        "generation": gen,
        "timestamp": datetime.now().isoformat(),
        "agents_trained": [],
        "merge_result": None,
    }

    # Step 1: Get recent task logs (async)
    task_logs = await memory.get_recent_tasks(limit=50)

    if len(task_logs) < 3:
        result["status"] = "skipped"
        result["reason"] = f"Not enough tasks ({len(task_logs)}/3 minimum)"
        return result

    await event_bus.emit(EventType.EVOLUTION_ROUND_START, {
        "generation": gen,
        "task_count": len(task_logs),
    })

    # Step 2: Generate training data
    sft_data = generate_sft_data(task_logs, min_score=0.6)

    if len(sft_data) < 5:
        result["status"] = "skipped"
        result["reason"] = f"Not enough quality data ({len(sft_data)}/5 minimum)"
        return result

    dataset_path = f"./logs/sft_gen{gen}.jsonl"
    save_dataset(sft_data, dataset_path)

    # Step 3: Train LoRA for key agents
    agents_to_train = ["coder", "architect", "critic"]
    trained_adapters = []

    for agent_name in agents_to_train:
        await event_bus.emit(EventType.TRAINING_STARTED, {
            "agent": agent_name,
            "generation": gen,
        })

        try:
            adapter_path = train_lora(
                agent_name=agent_name,
                dataset_path=dataset_path,
                generation=gen,
                max_steps=100,
            )

            trained_adapters.append({
                "name": agent_name,
                "path": adapter_path,
                "score": sum(d.get("score", 0) for d in sft_data) / len(sft_data),
            })
            result["agents_trained"].append(agent_name)

            # Register in Neo4j - matches 3-param signature: (name, role, model_version)
            agent_id = f"{agent_name}_gen{gen}"
            parent_id = f"{agent_name}_gen{gen - 1}" if gen > 1 else f"{agent_name}_gen0"

            await memory.add_agent(agent_id, agent_name, f"gen{gen}")
            if gen > 1:
                await memory.add_evolution_link(
                    parent_id, agent_id,
                    metrics={"method": "lora_finetune", "score": trained_adapters[-1]["score"]},
                )

            await event_bus.emit(EventType.TRAINING_COMPLETE, {
                "agent": agent_name,
                "generation": gen,
                "adapter_path": adapter_path,
            })

        except Exception as e:
            await event_bus.emit(EventType.ERROR, {
                "agent": agent_name,
                "error": str(e),
            })

    # Step 4: Merge top adapters (if we have at least 2)
    if len(trained_adapters) >= 2:
        try:
            parents = select_parents(
                [{"path": a["path"], "score": a["score"]} for a in trained_adapters],
                top_k=2,
            )

            merged_path = f"./models/lora/merged_gen{gen}"

            merge_loras(
                parent_paths=[p["path"] for p in parents],
                output_path=merged_path,
            )

            merged_id = f"merged_gen{gen}"
            await memory.add_agent(merged_id, "merged", f"gen{gen}")

            for adapter in trained_adapters[:2]:
                await memory.add_evolution_link(
                    f"{adapter['name']}_gen{gen}",
                    merged_id,
                    metrics={"method": "genetic_merge"},
                )

            result["merge_result"] = merged_path

            await event_bus.emit(EventType.MERGE_COMPLETE, {
                "generation": gen,
                "parents": [a["name"] for a in trained_adapters[:2]],
                "output": merged_path,
            })

        except Exception as e:
            await event_bus.emit(EventType.ERROR, {
                "phase": "merge",
                "error": str(e),
            })

    # Step 5: Broadcast lineage update
    await event_bus.emit(EventType.LINEAGE_UPDATE, {
        "generation": gen,
    })

    await event_bus.emit(EventType.EVOLUTION_ROUND_END, {
        "generation": gen,
        "agents_trained": result["agents_trained"],
        "status": "completed",
    })

    result["status"] = "completed"
    return result
