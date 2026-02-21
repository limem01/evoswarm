"""
LoRA adapter merging using MergeKit.
Implements genetic crossover: select top LoRAs, merge with weighted average.

MergeKit is primarily CLI-driven, so we generate YAML configs and invoke
the CLI programmatically.

VERIFIED API (Feb 2026):
- mergekit-yaml CLI with YAML config
- Supported methods: linear, slerp, ties, dare_linear, dare_ties
- 8B models fit easily on 16GB VRAM for merging
- --lazy-unpickle for memory optimization
"""
import os
import random
import subprocess
import tempfile
import yaml


def merge_loras(
    parent_paths: list[str],
    output_path: str,
    weights: list[float] | None = None,
    method: str = "linear",
    mutation_rate: float = 0.1,
) -> str:
    """
    Merge multiple LoRA adapters using genetic crossover.

    Args:
        parent_paths: List of paths to LoRA adapter directories
        output_path: Where to save the merged model
        weights: Optional explicit weights (default: equal + random mutation)
        method: Merge method (linear, slerp, ties, dare_ties)
        mutation_rate: Random weight perturbation magnitude

    Returns:
        Path to merged model
    """
    if len(parent_paths) < 2:
        raise ValueError("Need at least 2 parents to merge")

    # Generate weights with genetic mutation
    if weights is None:
        n = len(parent_paths)
        base_weight = 1.0 / n
        weights = [
            max(0.05, min(0.95, base_weight + random.uniform(-mutation_rate, mutation_rate)))
            for _ in range(n)
        ]
        # Normalize to sum to 1
        total = sum(weights)
        weights = [w / total for w in weights]

    # SLERP only supports exactly 2 models
    if method == "slerp" and len(parent_paths) != 2:
        method = "linear"

    # Build MergeKit YAML config
    config = {
        "models": [
            {
                "model": path,
                "parameters": {"weight": w},
            }
            for path, w in zip(parent_paths, weights)
        ],
        "merge_method": method,
        "dtype": "float16",
    }

    # Write config to temp file
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yml", delete=False
    ) as f:
        yaml.dump(config, f)
        config_path = f.name

    try:
        os.makedirs(output_path, exist_ok=True)

        # Run mergekit CLI
        result = subprocess.run(
            [
                "mergekit-yaml",
                config_path,
                output_path,
                "--lazy-unpickle",
            ],
            capture_output=True,
            text=True,
            timeout=300,  # 5 min timeout
        )

        if result.returncode != 0:
            raise RuntimeError(f"MergeKit failed: {result.stderr}")

        return output_path

    finally:
        os.unlink(config_path)


def select_parents(
    candidates: list[dict],
    top_k: int = 2,
    tournament_size: int = 3,
) -> list[dict]:
    """
    Tournament selection: pick top_k parents from candidates.

    Args:
        candidates: List of {"path": str, "score": float} dicts
        top_k: Number of parents to select
        tournament_size: Size of each tournament

    Returns:
        Selected parent dicts
    """
    selected = []
    for _ in range(top_k):
        tournament = random.sample(candidates, min(tournament_size, len(candidates)))
        winner = max(tournament, key=lambda c: c["score"])
        selected.append(winner)
    return selected
