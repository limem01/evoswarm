"""
LoRA fine-tuning using Unsloth (2026.2.1).
Optimized for RTX 5060 Ti (16GB VRAM).

VERIFIED API (Feb 2026):
- FastLanguageModel.from_pretrained(): load_in_4bit, max_seq_length, dtype
- FastLanguageModel.get_peft_model(): r, lora_alpha, target_modules
- SFTTrainer from trl 0.27.1 with SFTConfig
- Dataset format: {"messages": [{"role": ..., "content": ...}]}
"""
import os
import torch
from datasets import load_dataset


def train_lora(
    agent_name: str,
    dataset_path: str,
    generation: int,
    output_dir: str = "./models/lora",
    max_steps: int = 200,
):
    """
    Fine-tune a LoRA adapter for a specific agent.

    Args:
        agent_name: Name of the agent (e.g., "coder", "architect")
        dataset_path: Path to JSONL training data
        generation: Evolution generation number
        output_dir: Base directory for saving adapters
        max_steps: Training steps (200 = ~5min on RTX 5060 Ti)

    Returns:
        Path to saved LoRA adapter
    """
    # Import here to avoid loading CUDA until needed
    from unsloth import FastLanguageModel
    from trl import SFTTrainer, SFTConfig

    save_path = os.path.join(output_dir, f"{agent_name}_gen{generation}")

    # Step 1: Load base model in 4-bit
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name="unsloth/Meta-Llama-3.1-8B-Instruct-bnb-4bit",
        max_seq_length=2048,
        dtype=None,  # Auto-detect (bf16 on Blackwell)
        load_in_4bit=True,
        trust_remote_code=True,
    )

    # Step 2: Apply LoRA
    model = FastLanguageModel.get_peft_model(
        model,
        r=16,
        lora_alpha=16,
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        ],
        lora_dropout=0,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=3407,
    )

    # Step 3: Load dataset
    dataset = load_dataset("json", data_files=dataset_path, split="train")

    # Step 4: Configure training (RTX 5060 Ti optimized)
    training_config = SFTConfig(
        output_dir=save_path,
        per_device_train_batch_size=1,  # Conservative for 16GB
        gradient_accumulation_steps=4,  # Effective batch = 4
        warmup_steps=5,
        max_steps=max_steps,
        learning_rate=2e-4,
        bf16=torch.cuda.is_bf16_supported(),
        fp16=not torch.cuda.is_bf16_supported(),
        logging_steps=10,
        optim="paged_adamw_8bit",  # Memory-efficient optimizer
        weight_decay=0.01,
        lr_scheduler_type="linear",
        seed=3407,
        max_seq_length=2048,
        report_to="none",
    )

    # Step 5: Train
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        args=training_config,
    )

    trainer.train()

    # Step 6: Save LoRA adapter
    model.save_pretrained(save_path)
    tokenizer.save_pretrained(save_path)

    return save_path
