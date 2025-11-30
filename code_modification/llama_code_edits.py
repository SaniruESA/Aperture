import os
import traceback
from typing import Optional
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments, pipeline
from peft import LoraConfig, get_peft_model
from datasets import Dataset
import json

print(torch.__version__)

MODEL_NAME = "Salesforce/codet5-small"  # ~220M params

# Universal UI element types
UITypes = ["button", "text"]

file_endings = {"py": "Python", 
                "js": "JavaScript", 
                "tsx": "TypeScript"}

_pipe: Optional[pipeline] = None

# Load tokenizer and base model once
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, use_fast=True)

def tokenize(batch):
    return tokenizer(batch["text"], truncation=True, padding=False, max_length=512)  # reduced length

def loraed_model(lora_path: str):
    lora_config = LoraConfig(
        r=8,  # reduced rank
        lora_alpha=16, # reduced alpha
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM"
    )

    base = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME, 
        device_map="auto", 
        torch_dtype=torch.float16
    )
    model = get_peft_model(base, lora_config)
    model.print_trainable_parameters()

    # Load training data
    with open("code_modification/train.json", encoding="utf-8") as reader:
        raw_data = json.load(reader)

    entries = raw_data.get("train", [])
    if isinstance(entries, dict):
        entries = [entries]

    def build_text(record):
        instr = record.get("instruction:", "")
        response = record.get("response:", "")
        return instr + "\n" + response if instr or response else ""

    dataset = Dataset.from_list([{"text": build_text(entry)} for entry in entries])
    tokenized = dataset.map(tokenize, batched=True, remove_columns=["text"])

    # Training optimization
    training_args = TrainingArguments(
        output_dir="./codet5_lora",
        per_device_train_batch_size=1, # reduced batch size
        gradient_accumulation_steps=4, # accumulate gradients
        warmup_steps=50,
        max_steps=500, # shorter steps for testing
        learning_rate=2e-4,
        fp16=True, # use fp16 for GPU memory
        logging_steps=20,
        save_steps=200,
        optim="adamw_torch",
        report_to="none"
    )

    trainer = Trainer(model=model, args=training_args, train_dataset=tokenized)
    trainer.train()
    trainer.save_model()
    tokenizer.save_pretrained(lora_path)

def get_pipe():
    global _pipe
    if _pipe is not None:
        return _pipe

    try:
        model = AutoModelForCausalLM.from_pretrained(MODEL_NAME, device_map="auto", torch_dtype=torch.float16)
        _pipe = pipeline("text-generation", model=model, tokenizer=tokenizer, max_new_tokens=200, temperature=0.2)
        return _pipe
    except Exception:
        traceback.print_exc()
        raise

def string_to_single_line(input_string: str) -> str:
    lines = input_string.splitlines()
    stripped_lines = [line.strip().replace("\"", "\\\"") for line in lines if line.strip()]
    return '\\n'.join(stripped_lines)

def edit_code(filepath: str, output_path: str = None):
    with open(filepath, "r", encoding="utf-8") as f:
        original_code = f.read()

        # get code language 
        language = file_endings[filepath.split(".")[-1]] 
        
        # (temporary) - find the code framework 
        match language: 
            case "Python": 
                framework = "Tkinter" 
            case "JavaScript": 
                framework = "React" 
            case "TypeScript": 
                framework = "React" 
            case _: 
                framework = "React"

    prompt = f"""
        You are an expert accessibility engineer.
        Modify the following UI code to make elements accessible.
        Framework: {framework} ({language})
        RULES: Extract x,y,width,height, description, type, and add SERVER.add_button([...], description).
        ORIGINAL CODE START:
        {original_code}
        ORIGINAL CODE END
        MODIFIED CODE:
    """

    p = get_pipe()
    response = p(prompt)[0]["generated_text"]
    response = response.split("MODIFIED CODE:")[-1].strip()
    output_path = output_path or "build.py"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(response)
    print(f"Accessible version saved to: {output_path}")
    return response

if __name__ == "__main__":
    try:
        edit_code("testing_examples/TSA_Website/test.py")
    except Exception:
        traceback.print_exc()
