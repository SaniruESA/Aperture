import git_actions
import os
import json
import sys
import traceback


with open("supported.json", "r", encoding="utf-8") as file:
    supported_json = json.load(file)


def paste_aperture_executable(os: str):
    match os:
        case "Windows":
            shutil.copy("../dist/Aperture.exe", "local_repo")
        case "Mac":
            shutil.copy("../dist/Aperture", "local_repo")
            # TODO: ^^^^^^^^^^^ CHECK RIGHT FIL NAMMMMMMMMMME




# Goes through all files in a repo, and edits them
def edit_all_files(repo_link: str, entry_point_path: str = "", framework: str = "", target_os: str = "", testing=False):
    git_actions.clone_repo(repo_link, clone_dir="local_repo")

    frameworks = supported_json.get("frameworks", {})
    if framework and framework in frameworks:
        type_a = tuple(frameworks[framework].get("type_a", []))
        type_b = tuple(frameworks[framework].get("type_b", []))
    else:
        type_a = tuple()
        type_b = tuple()

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

    # run aperture helper only if an entry point is provided
    if entry_point_path:
        try:
            # import hf lazily to avoid triggering any HF login at module import
            import hf
            hf.run_aperture_code(os.path.join("local_repo", entry_point_path))
        except Exception:
            traceback.print_exc(file=sys.stderr)

    for root, _, files in os.walk("local_repo"):
        for file in files:

            if file.endswith(type_b):
                hf.generate_server_send_function(f"local_repo/{file}")
                hf.handle_conditional_ui(f"local_repo/{file}", full_ui_json)
                hf.eof_server_call(f"local_repo/{file}")
                hf.handle_alerts(f"local_repo/{file}")

    paste_aperture_executable(os)

    try:
        token = git_actions.authenticate_with_github()
    except Exception:
        token = None
        traceback.print_exc(file=sys.stderr)

    repo_name = repo_link.split("/")[-1].split(".")[0]
    git_actions.create_pull_request(repo_name=repo_name,
                                    branch_name="accessibility-updates",
                                    token=token)


# This will have multiple conditions later, just one communication for now
def handle_command(cmd: dict):
    action = cmd.get("action")
    if action == "run_edit_all":
        testing = bool(cmd.get("testing", False))
        try:
            edit_all_files(cmd.get("repo_link"), cmd.get("entry_point_path", ""), cmd.get("framework", ""), testing=testing)
            print(json.dumps({"status": "ok", "action": action}), flush=True)
        except Exception as e:
            traceback.print_exc(file=sys.stderr)
            sys.stderr.flush()
            print(json.dumps({"status": "error", "action": action, "error": str(e)}), flush=True)


if __name__ == "__main__":
    edit_all_files("https://github.com/D3BaNaNa/tkinter-test", "main.py", "Tkinter")
    # # keep taking stuff from 
    # if len(sys.argv) > 1:
    #     try:
    #         repo = sys.argv[1]
    #         entry = sys.argv[2] if len(sys.argv) > 2 else ""
    #         framework = sys.argv[3] if len(sys.argv) > 3 else ""
    #         testing = sys.argv[4].lower() == "true" if len(sys.argv) > 4 else True
    #         edit_all_files(repo, entry, framework, testing=testing)
    #         print(json.dumps({"status": "ok", "mode": "cli", "repo": repo}), flush=True)
    #     except Exception as e:
    #         traceback.print_exc(file=sys.stderr)
    #         sys.stderr.flush()
    #         print(json.dumps({"status": "error", "error": str(e)}), flush=True)
    # else:
    #     # keep reading otherwise
    #     for line in sys.stdin:
    #         line = line.strip()
    #         if not line:
    #             continue
    #         try:
    #             cmd = json.loads(line)
    #         except json.JSONDecodeError:
    #             print(json.dumps({"status": "error", "error": "invalid_json"}), flush=True)
    #             continue
    #         try:
    #             handle_command(cmd)
    #         except Exception as e:
    #             traceback.print_exc(file=sys.stderr)
    #             sys.stderr.flush()
    #             print(json.dumps({"status": "error", "error": str(e)}), flush=True)
