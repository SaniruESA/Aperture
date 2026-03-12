"""
Main file handling code editing for repo.
Takes repo and edits each file.

Runs when GH repo is inputted into Aperture.
"""

import git_actions
import os
import json
import sys
import traceback
import shutil
import hf
import platform


supported_json = {
    "frameworks": {
        "Flutter": {
            "type_a": [".dart"],
            "type_b": [".dart"]
        },
        "Qt (QML + C++)": {
            "type_a": [".qml", ".ui"],
            "type_b": [".cpp", ".h", ".qml"]
        },
        "Tkinter": {
            "type_a": [".py"],
            "type_b": [".py"]
        },
        "Electron": {
            "type_a": [".html", ".jsx", ".tsx"],
            "type_b": [".js", ".ts", ".jsx", ".tsx"]
        },
        "WPF": {
            "type_a": [".xaml"],
            "type_b": [".cs", ".xaml.cs"]
        },
        "WinForms": {
            "type_a": [".Designer.cs", ".resx"],
            "type_b": [".cs"]
        },
        "JavaFX": {
            "type_a": [".fxml"],
            "type_b": [".java"]
        },
        "Swing": {
            "type_a": [".java", ".form"],
            "type_b": [".java"]
        },
        "GTK (Python)": {
            "type_a": [".glade", ".ui"],
            "type_b": [".py"]
        },
        "GTK (C)": {
            "type_a": [".glade", ".ui"],
            "type_b": [".c", ".h"]
        },
        "wxWidgets (C++)": {
            "type_a": [".xrc"],
            "type_b": [".cpp", ".h"]
        },
        "wxPython": {
            "type_a": [".xrc"],
            "type_b": [".py"]
        },
        "Avalonia": {
            "type_a": [".axaml", ".xaml"],
            "type_b": [".cs", ".axaml.cs"]
        },
        "UWP": {
            "type_a": [".xaml"],
            "type_b": [".cs", ".xaml.cs"]
        },
        "Tauri": {
            "type_a": [".html", ".svelte", ".vue", ".jsx", ".tsx"],
            "type_b": [".js", ".ts", ".rs", ".jsx", ".tsx"]
        },
        "React Native (Windows/macOS)": {
            "type_a": [".jsx", ".tsx"],
            "type_b": [".js", ".ts", ".jsx", ".tsx"]
        },
        "MAUI": {
            "type_a": [".xaml"],
            "type_b": [".cs", ".xaml.cs"]
        },
        "Kivy": {
            "type_a": [".kv"],
            "type_b": [".py"]
        },
        "PyQt": {
            "type_a": [".ui", ".qml"],
            "type_b": [".py"]
        },
        "PySide": {
            "type_a": [".ui", ".qml"],
            "type_b": [".py"]
        },
        "Wails": {
            "type_a": [".html", ".svelte", ".vue", ".jsx", ".tsx"],
            "type_b": [".go", ".js", ".ts", ".jsx", ".tsx"]
        },
        "NW.js": {
            "type_a": [".html", ".jsx", ".tsx"],
            "type_b": [".js", ".ts", ".jsx", ".tsx"]
        },
        "Neutralinojs": {
            "type_a": [".html"],
            "type_b": [".js", ".ts"]
        },
        "Lazarus/Free Pascal": {
            "type_a": [".lfm", ".dfm"],
            "type_b": [".pas", ".pp"]
        },
        "Dear ImGui": {
            "type_a": [".cpp", ".h"],
            "type_b": [".cpp", ".h"]
        },
        "FLTK": {
            "type_a": [".fl"],
            "type_b": [".cpp", ".cxx", ".h"]
        },
        "Tcl/Tk": {
            "type_a": [".tcl"],
            "type_b": [".tcl"]
        },
        "Xojo": {
            "type_a": [".xojo_window"],
            "type_b": [".xojo_code"]
        },
        "Eto.Forms": {
            "type_a": [".eto", ".jeto", ".xeto"],
            "type_b": [".cs"]
        },
        "Slint": {
            "type_a": [".slint"],
            "type_b": [".rs", ".cpp", ".js"]
        }
    }
}






try:
    token = git_actions.authenticate_with_github()
except Exception:
    token = None
    traceback.print_exc(file=sys.stderr)

def paste_aperture_executable(os_used: str):

    os_used = platform.system().lower()

    match os_used:
        case "windows":
            shutil.copy("lib_build/aperture.exe", "local_repo")
        case "darwin":
            shutil.copy("lib_build/aperture", "local_repo")




# Goes through all files in a repo, and edits them
def edit_all_files(repo_link: str, entry_point_path: str = "", framework: str = "", os_used: str = "", testing: bool = False):

    
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

    with open("local_repo/ui_elements.json","w") as fp:
        json.dump(full_ui_json, fp, indent=4)

    # run aperture helper only if an entry point is provided
    if entry_point_path:
        try:
            # import hf lazily to avoid triggering any HF login at module import
            pass
            hf.run_aperture_code(os.path.join("local_repo", entry_point_path))
        except Exception:
            traceback.print_exc(file=sys.stderr)

    for root, _, files in os.walk("local_repo"):
        for file in files:

            if file.endswith(type_b):
                pass
                hf.generate_server_send_function(f"local_repo/{file}")
                hf.handle_conditional_ui(f"local_repo/{file}", full_ui_json)
                hf.eof_server_call(f"local_repo/{file}")
                hf.handle_alerts(f"local_repo/{file}")


    paste_aperture_executable(os_used)

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
    # If CLI args provided, run once (CLI mode)
    if len(sys.argv) > 1:
        try:
            repo = sys.argv[1]
            entry = sys.argv[2] if len(sys.argv) > 2 else ""
            framework = sys.argv[3] if len(sys.argv) > 3 else ""
            testing = sys.argv[4].lower() == "true" if len(sys.argv) > 4 else True
            edit_all_files(repo, entry, framework, testing=testing)
            print(json.dumps({"status": "ok", "mode": "cli", "repo": repo}), flush=True)
        except Exception as e:
            traceback.print_exc(file=sys.stderr)
            sys.stderr.flush()
            print(json.dumps({"status": "error", "error": str(e)}), flush=True)
    else:
        # Run as a long-running child process: read JSON commands from stdin
        try:
            for line in sys.stdin:
                line = line.strip()
                if not line:
                    continue
                try:
                    cmd = json.loads(line)
                except json.JSONDecodeError:
                    print(json.dumps({"status": "error", "error": "invalid_json"}), flush=True)
                    continue
                try:
                    handle_command(cmd)
                except Exception as e:
                    traceback.print_exc(file=sys.stderr)
                    sys.stderr.flush()
                    print(json.dumps({"status": "error", "error": str(e)}), flush=True)
        except Exception:
            traceback.print_exc(file=sys.stderr)