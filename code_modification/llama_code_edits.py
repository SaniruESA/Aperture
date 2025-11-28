import os
import traceback
from typing import Optional
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

# Set the model name via env var for easy testing/fallbacks
MODEL_NAME = os.environ.get("LLAMA_MODEL_NAME", "bigcode/starcoder2-3b")

# Make this a universal value across all files later (its repeated in keyborad_nav)
UITypes = ["button", "text"]

file_endings = {
    "py": "Python",
    "js": "JavaScript",
    "tsx": "TypeScript"
}

_pipe: Optional[pipeline] = None


def get_pipe():
    """Lazily create and cache the HF text-generation pipeline.

    Avoids loading large models at import time which can crash the process
    (especially on Windows / when GPU drivers / CUDA are not configured).
    """
    global _pipe
    if _pipe is not None:
        return _pipe

    try:
        # Prefer GPU if available; otherwise use CPU
        if torch.cuda.is_available():
            # Let transformers/accelerate place layers automatically
            tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
            model = AutoModelForCausalLM.from_pretrained(
                MODEL_NAME,
                device_map="auto",
                dtype="auto",
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
            tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
            model = AutoModelForCausalLM.from_pretrained(
                MODEL_NAME,
                device_map={"": "cpu"},
            )
            _pipe = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
                device=-1,
                max_new_tokens=800,
                temperature=0.2,
            )

        return _pipe
    except Exception as e:
        # Provide a readable error and re-raise so callers can decide what to do.
        print("Failed to create model pipeline:")
        traceback.print_exc()
        raise

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
        edit_code("testing_examples/TSA_Website/page.tsx")
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
