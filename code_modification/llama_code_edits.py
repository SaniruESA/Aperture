import os
import traceback
from typing import Optional
import torch

print(torch.__version__)

from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, pipeline, TrainingArguments
from peft import LoraConfig, get_peft_model

# Set the model name via env var for easy testing/fallbacks
MODEL_NAME = "Qwen/Qwen3-1.7B"

# Make this a universal value across all files later (its repeated in keyborad_nav)
UITypes = ["button", "text"]

file_endings = {
    "py": "Python",
    "js": "JavaScript",
    "tsx": "TypeScript"
}

_pipe: Optional[pipeline] = None

model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    torch_dtype="auto",
    device_map="auto"
)

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, use_fast=True)

def tokenize(batch):
    return tokenizer(
        batch["text"],
        truncation=True,
        padding=False,
        max_length=2048
    )

def loraed_model(lora_path: str):
    lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
    )

    base = AutoModelForCausalLM.from_pretrained(MODEL_NAME, device_map="auto")
    model = get_peft_model(base, lora_config)
    model.print_trainable_parameters()

    import json
    from datasets import Dataset

    with open("code_modification/train.json", encoding="utf-8") as reader:
        raw_data = json.load(reader)

    entries = raw_data.get("train")
    if entries is None:
        raise RuntimeError("train.json must contain a top-level 'train' entry")

    if isinstance(entries, dict):
        entries = [entries]

    def build_text(record):
        instr = record.get("instruction:", "")
        response = record.get("response:", "")
        return instr + "\n" + response if instr or response else ""

    dataset = Dataset.from_list([{"text": build_text(entry)} for entry in entries])
    tokenized = dataset.map(tokenize, batched=True, remove_columns=["text"])
    training_args = TrainingArguments(
        output_dir="./qwen3_lora",
        per_device_train_batch_size=2,
        gradient_accumulation_steps=8,
        warmup_steps=50,
        max_steps=1000,
        learning_rate=2e-4,
        fp16=True,
        logging_steps=20,
        save_steps=200,
        optim="adamw_torch",
        report_to="none"
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized,
    )

    trainer.train()

    trainer.save_model()

    tokenizer.save_pretrained(lora_path)









def get_pipe():
    """Lazily create and cache the HF text-generation pipeline.

    Avoids loading large models at import time which can crash the process
    (especially on Windows / when GPU drivers / CUDA are not configured).
    """
    loraed_model("qwen3_lora")
    global _pipe
    if _pipe is not None:
        return _pipe

    try:
        # Prefer GPU if available; otherwise use CPU
        # Qwen-family models on Hugging Face often require `trust_remote_code=True`
        # and benefit from explicit dtype settings when using CUDA
        if torch.cuda.is_available():
            # Let transformers/accelerate place layers automatically and use fp16 on GPU
            tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True, use_fast=False)
            model = AutoModelForCausalLM.from_pretrained(
                MODEL_NAME,
                trust_remote_code=True,
                device_map="auto",
                torch_dtype=torch.float16,
                low_cpu_mem_usage=True,
            )
            _pipe = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
                max_new_tokens=800,
                temperature=0.2,
            )
        else:
            # Force CPU to avoid driver/CUDA issues on machines without a proper GPU setup
            # Load with trust_remote_code so custom model/tokenizer classes are available
            tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True, use_fast=False)
            model = AutoModelForCausalLM.from_pretrained(
                MODEL_NAME,
                trust_remote_code=True,
                device_map={"": "cpu"},
                low_cpu_mem_usage=True,
            )
            _pipe = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
                max_new_tokens=800,
                temperature=0.2,
            )

        return _pipe
    except Exception as e:
        # Provide a readable error and re-raise so callers can decide what to do.
        print("Failed to create model pipeline:")
        traceback.print_exc()
        print("Hint: For Qwen models you may need internet access, the latest `transformers`, and `trust_remote_code=True`.\n"
              "On GPU, ensure CUDA drivers are installed; on CPU consider using a smaller model or enable swap if memory is low.")
        raise

def string_to_single_line(input_string: str) -> str:
    """Convert a multi-line string to a single line by removing newlines and extra spaces."""
    lines = input_string.splitlines()
    stripped_lines = [line.strip().replace("\"", "\\\"") for line in lines if line.strip()]
    single_line_string = '\\n'.join(stripped_lines)
    return single_line_string

def edit_code(filepath: str, output_path: str = None):
    """
    Reads UI code from `filepath`, uses a HF transformer to modify it
    adding accessibility registration (aria/description + bounding box).
    """

    # Read original code
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

    # Prompt the model to modify code
    prompt = f"""
        You are an expert accessibility engineer and software developer.

        TASK:
        Take the following UI code and modify it to make UI elements accessible.
        Framework: {framework} ({language})

        RULES:
        - For every button, label, textbox, checkbox, entry, menu, or widget:
            - Extract its x,y,width,height if present
            - Extract its description - should be short (e.g., "Submit button", "Username field", etc.)
            - Find the type of the UI element (choose from: {UITypes})
            - Register the widget by adding a function call based on UI element types:
                - For button: SERVER.add_button([x, y, width, height], description)
            - Cumulate these function calls in your output

        RETURN:
        Return every function call, separated by new lines.

        ---------------------------
        ORIGINAL CODE START:
        {original_code}
        ---------------------------
        MODIFIED CODE:
    """

    print(string_to_single_line("""SERVER.add_button([900, 120, 40, 40], "Close registration popup");
SERVER.add_button([700, 300, 200, 40], "Go to Registration");
SERVER.add_button([1000, 400, 120, 40], "View Details for first upcoming event");
SERVER.add_button([1000, 460, 120, 40], "View Details for second upcoming event");
SERVER.add_button([1000, 520, 120, 40], "View Details for third upcoming event");
SERVER.add_button([100, 600, 180, 50], "View All Events");
SERVER.add_button([300, 600, 180, 50], "My Profile");
SERVER.add_button([500, 600, 180, 50], "Register");
SERVER.add_button([700, 600, 180, 50], "Contact Us");
SERVER.add_button([960, 200, 200, 50], "Add Announcement");
SERVER.add_button([1080, 220, 40, 40], "Close Add Announcement Modal");
SERVER.add_button([960, 300, 200, 50], "Save Announcement");
SERVER.add_button([150, 800, 40, 40], "Calendar Day 1 Event");
SERVER.add_button([200, 800, 40, 40], "Calendar Day 2 Event");
SERVER.add_button([250, 800, 40, 40], "Calendar Day 3 Event"); """))
    print(string_to_single_line(prompt))

    # Create/get the pipeline at runtime w/ safe lazy load
    p = get_pipe()

    # call the pipeline to generate the modified code
    response = p(prompt)[0]["generated_text"]

    # Extract just the modified part if needed (after prompt)
    if "MODIFIED CODE:" in response:
        response = response.split("MODIFIED CODE:")[1].strip()

    # Save to output file
    output_path = "build.py"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(response)

    print(f"Accessible version saved to: {output_path}")

    return response

# For testing purposes
if __name__ == "__main__":
    try:
        edit_code("testing_examples/TSA_Website/test.py")
    except Exception:
        print("edit_code failed during execution")
        traceback.print_exc()




# goes through all files in a repo, and edits them
def edit_all_files(repo_dir: str):
    for root, _, files in os.walk(repo_dir):
        for file in files:
            # update to add the many different file types (potentially an ignore list?)
            if file.endswith((".txt", ".py")):
                edit_code(os.path.join(root, file))

            # LOG HERE:
            # info(f"Edited {file}", __name__)


# TODO: 
# llama integration - Currently, just loops thru files in a repo and replaces "software" with "tsa"
# logs and info
# ignore list of files (currently, it temporarily accepts only .txt and .py)