
"""
Main module for the code modification tool.Handles cmds from Electron main process, coordinates the overall flow of cloning repos, editing files, and creating pull requests.
Contains utility functions for file operations and command handling. Also emits telemetry to stdout
"""

import os
import sys
import json
import shutil
import traceback
import platform

import git_actions

def resource_path(rel_path: str) -> str:
    """Return absolute path to a resource"""
    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", os.path.dirname(__file__))
    else:
        base = os.path.dirname(__file__)
    return os.path.join(base, rel_path)

def load_supported() -> dict:
    """Load supported.json from resources"""
    try:
        with open(resource_path("supported.json"), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        traceback.print_exc(file=sys.stderr)
        return {}

supported_json = load_supported()

def send_progress(text: str):
    """Emit a progress json object on stdout."""
    try:
        print(json.dumps({"action": "progress", "text": str(text)}), flush=True)
    except Exception:
        traceback.print_exc(file=sys.stderr)

def paste_aperture_executable():
    """Try to copy a prebuilt Aperture helper into local_repo if available."""
    candidates = [
        resource_path("lib_build/aperture"),
        resource_path("lib_build/aperture.exe"),
        os.path.join(os.path.dirname(__file__), "lib_build", "aperture"),
        os.path.join(os.path.dirname(__file__), "lib_build", "aperture.exe"),
        os.path.join(os.path.dirname(__file__), "..", "dist", "Aperture"),
        os.path.join(os.path.dirname(__file__), "..", "website", "build", "python", "mac", "Aperture"),
        os.path.join(os.path.dirname(__file__), "..", "website", "build", "python", "win", "Aperture.exe"),
    ]

    want_exe = platform.system().lower().startswith("win")
    found = None
    for c in candidates:
        if not c:
            continue
        if os.path.exists(c):
            found = c
            break
        if want_exe and os.path.exists(c + ".exe"):
            found = c + ".exe"
            break

    if not found:
        send_progress("Aperture helper not found; skipping insertion")
        return

    try:
        os.makedirs("local_repo", exist_ok=True)
        dst = os.path.join("local_repo", os.path.basename(found))
        shutil.copy(found, dst)
        try:
            os.chmod(dst, 0o755)
        except Exception:
            pass
        send_progress(f"Inserted Aperture helper from {found}")
    except Exception:
        traceback.print_exc(file=sys.stderr)
        send_progress("Failed to insert Aperture helper")

def edit_all_files(repo_link: str, entry_point_path: str = "", framework: str = "", os_used: str = "", testing: bool = False):
    """edit all the file"""
    send_progress("Starting edit_all_files")
    send_progress("Cloning repository")
    try:
        git_actions.clone_repo(repo_link, clone_dir="local_repo")
        send_progress("Repository cloned")
    except Exception as e:
        traceback.print_exc(file=sys.stderr)
        send_progress(f"Failed to clone repository: {e}")
        raise

    frameworks = supported_json.get("frameworks", {})
    if framework and framework in frameworks:
        type_a = tuple(frameworks[framework].get("type_a", []))
        type_b = tuple(frameworks[framework].get("type_b", []))
    else:
        type_a = tuple()
        type_b = tuple()

    full_ui_json = {}

    # Lazy import of hf to avoid auth prompt at startup
    hf = None
    try:
        import hf as _hf
        hf = _hf
    except Exception:
        send_progress("hf module not available; skipping HF steps")

    # Detect UI elements (type_a)
    scanned = 0
    if hf and type_a:
        send_progress("Detecting UI elements")
        for root, _, files in os.walk("local_repo"):
            for fname in files:
                if fname.endswith(type_a):
                    scanned += 1
                    fpath = os.path.join(root, fname)
                    try:
                        resp = hf.detect_ui_elements(fpath)
                        if isinstance(resp, dict):
                            full_ui_json[fpath] = resp
                            send_progress(f"Detected UI in {fname}")
                    except Exception:
                        traceback.print_exc(file=sys.stderr)
        send_progress(f"UI detection complete ({scanned} files scanned)")
    else:
        send_progress("Skipping UI detection")

    try:
        os.makedirs("local_repo", exist_ok=True)
        with open(os.path.join("local_repo", "ui_elements.json"), "w", encoding="utf-8") as fp:
            json.dump(full_ui_json, fp, indent=2)
        send_progress("Wrote ui_elements.json")
    except Exception:
        traceback.print_exc(file=sys.stderr)
        send_progress("Failed to write ui_elements.json")

    # Run aperture helper on entry point if provided
    if entry_point_path and hf:
        try:
            send_progress(f"Running aperture helper on {entry_point_path}")
            hf.run_aperture_code(os.path.join("local_repo", entry_point_path))
            send_progress("Aperture helper finished")
        except Exception:
            traceback.print_exc(file=sys.stderr)
            send_progress("Aperture helper failed")
    elif entry_point_path and not hf:
        send_progress("Entry point provided but hf missing; skipping aperture run")

    # type_b edits via hf
    if hf and type_b:
        send_progress("Applying type_b edits")
        for root, _, files in os.walk("local_repo"):
            for fname in files:
                if fname.endswith(type_b):
                    try:
                        fpath = os.path.join(root, fname)
                        hf.generate_server_send_function(fpath)
                        hf.handle_conditional_ui(fpath, full_ui_json)
                        hf.eof_server_call(fpath)
                        hf.handle_alerts(fpath)
                        send_progress(f"Edited {fname}")
                    except Exception:
                        traceback.print_exc(file=sys.stderr)
        send_progress("Type_b edits complete")
    else:
        send_progress("Skipping type_b edits")

    # Insert Aperture helper if available
    paste_aperture_executable()

    # Build owner/repo string
    repo_full = repo_link
    try:
        if repo_link.startswith("http://") or repo_link.startswith("https://"):
            parts = repo_link.rstrip("/").split("/")
            owner = parts[-2]
            repo = parts[-1].replace(".git", "")
            repo_full = f"{owner}/{repo}"
        else:
            repo_full = repo_link.strip()
    except Exception:
        pass

    send_progress(f"Preparing pull request for {repo_full}")

    # Authenticate and create PR
    try:
        token = git_actions.authenticate_with_github()
    except Exception:
        token = None
        traceback.print_exc(file=sys.stderr)
        send_progress("GitHub authentication failed")

    try:
        git_actions.create_pull_request(repo_name=repo_full, branch_name="accessibility-updates", token=token)
        send_progress("Pull request created")
    except Exception as e:
        traceback.print_exc(file=sys.stderr)
        send_progress(f"Failed to create pull request: {e}")
        raise

def handle_command(cmd: dict):
    action = cmd.get("action")
    if action == "run_edit_all":
        testing = bool(cmd.get("testing", False))
        try:
            edit_all_files(
                cmd.get("repo_link"),
                cmd.get("entry_point_path", ""),
                cmd.get("framework", ""),
                cmd.get("os_used", ""),
                testing=testing,
            )
            print(json.dumps({"status": "ok", "action": action}), flush=True)
        except Exception as e:
            traceback.print_exc(file=sys.stderr)
            sys.stderr.flush()
            print(json.dumps({"status": "error", "action": action, "error": str(e)}), flush=True)
    else:
        print(json.dumps({"status": "unknown_action", "action": action}), flush=True)

if __name__ == "__main__":
    # If CLI args provided, run once (CLI mode)
    if len(sys.argv) > 1:
        try:
            repo = sys.argv[1]
            entry = sys.argv[2] if len(sys.argv) > 2 else ""
            framework = sys.argv[3] if len(sys.argv) > 3 else ""
            testing = sys.argv[4].lower() == "true" if len(sys.argv) > 4 else False
            edit_all_files(repo, entry, framework, testing=testing)
            print(json.dumps({"status": "ok", "mode": "cli", "repo": repo}), flush=True)
        except Exception as e:
            traceback.print_exc(file=sys.stderr)
            sys.stderr.flush()
            print(json.dumps({"status": "error", "error": str(e)}), flush=True)
    else:
        # Run as a long-running child process: read JSON commands from stdin
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
