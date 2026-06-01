from __future__ import annotations

import argparse
from pathlib import Path

from datasets import load_dataset
from peft import LoraConfig
from peft import get_peft_model
from transformers import AutoModelForCausalLM, AutoTokenizer, DataCollatorForLanguageModeling, Trainer, TrainingArguments


def format_example(example: dict[str, str]) -> str:
    return format_prompt(example) + example["sql"]


def format_prompt(example: dict[str, str]) -> str:
    return f"""### Instruction
{example["instruction"]}

### Schema
{example["schema"]}

### Question
{example["question"]}

### SQL
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Train a SchemaSage LoRA Text2SQL adapter.")
    parser.add_argument("--base-model", default="Qwen/Qwen2.5-Coder-0.5B-Instruct")
    parser.add_argument("--train-file", default="data/training/demo_text2sql.jsonl")
    parser.add_argument("--output-dir", default="artifacts/lora/schemasage-qwen-0.5b-adapter")
    parser.add_argument("--epochs", type=float, default=3.0)
    parser.add_argument("--learning-rate", type=float, default=2e-4)
    parser.add_argument("--rank", type=int, default=8)
    parser.add_argument("--max-seq-length", type=int, default=768)
    parser.add_argument("--limit", type=int, default=0, help="Optional cap for quick training runs.")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    train_path = Path(args.train_file)
    if not train_path.exists():
        raise FileNotFoundError(f"Training file not found: {train_path}")

    dataset = load_dataset("json", data_files=str(train_path), split="train")
    if args.limit:
        dataset = dataset.shuffle(seed=args.seed).select(range(min(args.limit, len(dataset))))
    tokenizer = AutoTokenizer.from_pretrained(args.base_model, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(args.base_model, trust_remote_code=True)
    model.config.use_cache = False

    peft_config = LoraConfig(
        r=args.rank,
        lora_alpha=args.rank * 2,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    )
    model = get_peft_model(model, peft_config)

    def tokenize_example(example: dict[str, str]) -> dict[str, list[int]]:
        prompt = format_prompt(example)
        text = prompt + example["sql"] + tokenizer.eos_token
        tokenized = tokenizer(
            text,
            truncation=True,
            max_length=args.max_seq_length,
            padding=False,
        )
        prompt_token_count = len(
            tokenizer(
                prompt,
                truncation=True,
                max_length=args.max_seq_length,
                padding=False,
            )["input_ids"]
        )
        labels = tokenized["input_ids"].copy()
        labels[:prompt_token_count] = [-100] * min(prompt_token_count, len(labels))
        tokenized["labels"] = labels
        return tokenized

    tokenized_dataset = dataset.map(
        tokenize_example,
        remove_columns=dataset.column_names,
    )
    training_args = TrainingArguments(
        output_dir=args.output_dir,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=4,
        learning_rate=args.learning_rate,
        logging_steps=1,
        save_strategy="epoch",
        report_to=[],
        seed=args.seed,
    )

    trainer = Trainer(
        model=model,
        train_dataset=tokenized_dataset,
        args=training_args,
        data_collator=DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False),
    )
    trainer.train()
    trainer.model.save_pretrained(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)


if __name__ == "__main__":
    main()
