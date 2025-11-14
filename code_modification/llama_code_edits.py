import os
# from ..python_stuff.python_acc_lib.logger.basic_logs import *

def edit_code(file_path):
    print(f"{file_path=}")
    with open(file_path, "r", encoding="utf-8") as f:
        code = f.read()

    modified_code = code.replace("software", "tsa")

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(modified_code)

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