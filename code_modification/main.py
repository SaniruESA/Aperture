import llama_code_edits
import git_actions 
import os   
import json
import sys

with open("../supported.json", "r", encoding="utf-8") as file:
    supported_json = json.load(file)
    frameworks = supported_json["frameworks"]

# Goes through all files in a repo, and edits them
def edit_all_files(repo_link: str, entry_point_path: str, framework: str, testing=False):

    git_actions.clone_repo(repo_link, clone_dir="local_repo")

    for root, _, files in os.walk("local_repo"):
        for file in files:
            # update to add the many different file types (potentially an ignore list)
            if file.endswith(tuple(frameworks[framework]["file_extensions"].split(", "))):
                if not testing:
                    llama_code_edits.edit_code(os.path.join(root, file))
                else:
                    llama_code_edits.edit_code_test(os.path.join(root, file))

            # LOG HERE
            # info(f"Edited {file}, __name__")

    # Extracts repo name from full link
    repo_name = repo_link.split("/")[-1].split(".")[0]

    # PR on accessibility-updates branch
    git_actions.create_pull_request(repo_name=repo_name, 
                                    branch_name="accessibility-updates")
# This will have multiple conditions later, just one communication for now
def handle_command(cmd: dict):
    action = cmd.get("action")
    if action == "run_edit_all":
        testing = bool(cmd.get("testing", False))
        edit_all_files(cmd.get("repo_link"), cmd.get("entry_point_path", ""), cmd.get("framework", ""), testing=testing)

if __name__ == "__main__":
    # detects args (excludes script name) 
    if len(sys.argv) > 1:
        edit_all_files(sys.argv[1], testing=True)
    else: # keep reading commands otherwise
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                cmd = json.loads(line)
                handle_command(cmd)