import git_actions 
import os   
import json
import sys
import hf

TOKEN = git_actions.authenticate_with_github()

# TEMPORARY FUNCTION
def edit_code_test(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        code = f.read()

    modified_code = code + "1/17/26"

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(modified_code)



with open("supported.json", "r", encoding="utf-8") as file:
    supported_json = json.load(file)

# Goes through all files in a repo, and edits them
def edit_all_files(repo_link: str, entry_point_path: str, framework: str, testing=False):

    git_actions.clone_repo(repo_link, clone_dir="local_repo")

    type_a = tuple(supported_json["frameworks"][framework]["type_a"])
    type_b = tuple(supported_json["frameworks"][framework]["type_b"])

    # generating ui_elements.json
    full_ui_json = {}

    for root, _, files in os.walk("local_repo"):
        for file in files:

            if file.endswith(type_a):
                response = hf.detect_ui_elements(f"local_repo/{file}")

                for key, value in response.items():
                    full_ui_json[key] = value

    with open("ui_elements.json","w") as fp:
        json.dump(full_ui_json, fp, indent=4)
    # TODO: generate json file

    # Code to run Aperture executable
    hf.run_aperture_code(os.path.join("local_repo", entry_point_path))

    for root, _, files in os.walk("local_repo"):
        for file in files:

            if file.endswith(type_b):
                hf.generate_server_send_function(f"local_repo/{file}")
                hf.handle_conditional_ui(f"local_repo/{file}", full_ui_json)
                hf.eof_server_call(f"local_repo/{file}")
                hf.handle_alerts(f"local_repo/{file}")

    # Extracts repo name from full link
    repo_name = repo_link.split("/")[-1].split(".")[0]

    # PR on accessibility-updates branch
    git_actions.create_pull_request(repo_name=repo_name, branch_name="accessibility-updates", token=TOKEN)


# This will have multiple conditions later, just one communication for now
def handle_command(cmd: dict):
    action = cmd.get("action")
    if action == "run_edit_all":
        testing = bool(cmd.get("testing", False))
        edit_all_files(cmd.get("repo_link"), cmd.get("entry_point_path", ""), cmd.get("framework", ""), testing=testing)

# if __name__ == "__main__":
#     # detects args (excludes script name) 
#     if len(sys.argv) > 1:
#         edit_all_files(sys.argv[1], testing=True)
#     else: # keep reading commands otherwise
#         for line in sys.stdin:
#             line = line.strip()
#             if not line:
#                 continue
#             try:
#                 cmd = json.loads(line)
#                 handle_command(cmd)
#             except:
#                 pass

if __name__ == "__main__":
    edit_all_files("https://github.com/D3BaNaNa/flutter-test", "lib/main.dart", "Qt (QML + C++)")