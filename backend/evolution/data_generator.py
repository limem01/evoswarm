"""
Generate synthetic SFT training data from agent task logs.
Uses LLM-as-judge to score agent outputs and create training pairs.

Dataset format: ChatML messages format (required by TRL SFTTrainer + Unsloth).
[{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
"""
import json
import os
from langchain_ollama import ChatOllama


def generate_sft_data(
    task_logs: list[dict],
    min_score: float = 0.7
) -> list[dict]:
    """
    Convert task logs into SFT training examples.

    Args:
        task_logs: List of {prompt, outcome, agent_scores} dicts from Neo4j
        min_score: Minimum quality score to include in training data

    Returns:
        List of {"messages": [{"role": ..., "content": ...}]} dicts
    """
    llm = ChatOllama(
        model=os.getenv("OLLAMA_MODEL", "llama3.1:8b-instruct-q4_K_M"),
        temperature=0.0,
    )

    sft_examples = []

    for log in task_logs:
        prompt = log.get("prompt", "")
        outcome = log.get("outcome", "")

        if not prompt or not outcome:
            continue

        # Use LLM as judge to score the outcome
        judge_prompt = f"""Score this agent's response on a scale of 0.0 to 1.0.
Consider: correctness, completeness, clarity, and usefulness.

Task: {prompt}

Agent Response: {outcome[:2000]}

Respond with ONLY a number between 0.0 and 1.0."""

        try:
            response = llm.invoke(judge_prompt)
            score_text = response.content.strip()
            # Extract numeric score
            score = float("".join(c for c in score_text if c in "0123456789."))
            score = min(1.0, max(0.0, score))
        except (ValueError, AttributeError):
            score = 0.5  # Default if judge fails

        if score >= min_score:
            sft_examples.append({
                "messages": [
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": outcome},
                ],
                "score": score,
            })

    return sft_examples


def generate_preference_pairs(task_logs: list[dict]) -> list[dict]:
    """
    Generate DPO preference pairs from task logs.
    Creates (chosen, rejected) pairs by comparing high-score vs low-score
    responses to similar prompts.

    Returns:
        List of {"prompt": [...], "chosen": [...], "rejected": [...]} dicts
    """
    # Group by similar prompts (simplified: same first 50 chars)
    groups: dict[str, list] = {}
    for log in task_logs:
        key = log.get("prompt", "")[:50]
        groups.setdefault(key, []).append(log)

    pairs = []
    for key, logs in groups.items():
        if len(logs) < 2:
            continue

        # Sort by score (best first)
        scored = sorted(
            logs,
            key=lambda x: float(x.get("score", 0)),
            reverse=True
        )
        best = scored[0]
        worst = scored[-1]

        pairs.append({
            "prompt": [{"role": "user", "content": best["prompt"]}],
            "chosen": [{"role": "assistant", "content": best["outcome"]}],
            "rejected": [{"role": "assistant", "content": worst["outcome"]}],
        })

    return pairs


def save_dataset(examples: list[dict], output_path: str):
    """Save training data as JSONL file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for ex in examples:
            f.write(json.dumps(ex) + "\n")
