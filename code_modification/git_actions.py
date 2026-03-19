# DEPENDENCIES REQUIRED: stuff for PyGithub, GitPython
"""
This module contains functions for interacting with GitHub, including authentication, cloning repos, committing changes, and creating releases. It uses the PyGithub library for GitHub API interactions and GitPython for local git operations.
"""
from github import Github, Auth, GithubException
from git import Repo
import git as gitlib
import os
import time
import requests
import subprocess
try:
    from requests.adapters import HTTPAdapter
except Exception:
    HTTPAdapter = None

try:
    from urllib3.util.retry import Retry
except Exception:
    Retry = None
import stat
import webbrowser
import json
import pyperclip
import shutil
import traceback
import sys
import tempfile

# Aperture project ID
CLIENT_ID = "Ov23liV0UHREdct0ILC3"


def authenticate_with_github():
    """
    Authenticates the user with GitHub; It opens the GitHub authentication page in the user's browser and polls for an access token until the user completes authentication.
    """
    # Post json request
    res = requests.post(
        "https://github.com/login/device/code",
        headers={"Accept": "application/json"},
        data={
            "client_id": CLIENT_ID,
            "scope": "repo read:user"
        }
    ).json()

    # Get user code from result request, copy to clipboard
    user_code = res["user_code"]
    pyperclip.copy(user_code)

    print("The GitHub authentication page will open shortly.")
    print(f"Your code ({user_code}) has already been copied to your clipboard, you just need to paste it.")

    try:
        # Print JSON structured message for Electron to receive
        print(json.dumps({"action": "open_url", "url": res["verification_uri"]}), flush=True)
    except Exception:
        # try to open directly as a fallback
        webbrowser.open(res["verification_uri"]) 

    device_code = res["device_code"]
    interval = res.get("interval", 5)

    while True:

        # Post request for access token
        token_res = requests.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": CLIENT_ID,
                "device_code": device_code,
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code"
            }
        ).json()

        # Get Github access token
        if "access_token" in token_res:
            return token_res["access_token"]

        # Error handling, ignore pending authorization or too fast errors
        if token_res.get("error") not in ("authorization_pending", "slow_down"):
            raise RuntimeError(token_res)

        time.sleep(interval)


def remove_readonly(func, path, ex_info):
    """ 
    Removes read-only attribute from files to allow deletion

    Arguments:
        func: The function to call after changing permissions (e.g., os.remove)
        path: The path of the file to change permissions for
        ex_info: Exception info (not used)
    """
    os.chmod(path, stat.S_IWRITE)
    func(path)


def clone_repo(repo_url, clone_dir="local_repo"):
    """
    Clones a GitHub repository to a local directory. If the directory already exists, it deletes it first.

    Arguments:
        repo_url: The URL of the GitHub repository to clone
        clone_dir: The local directory to clone the repository into (default: "local_repo")
    """
    # Delete a repo if it already exists
    if os.path.exists(clone_dir):
        print("Local repo clone exists, deleting and replacing")
        shutil.rmtree(clone_dir, onexc=remove_readonly)

    # Clone repo into the directory provided
    Repo.clone_from(repo_url, clone_dir)
    print(f"Cloned {repo_url}")
    return clone_dir


def stage_and_commit(repo_dir, commit_message="Added all accessibility features", remote_name="origin") -> bool:
    """
    Stages all changes in the local repository, commits them with a message, and pushes the changes to a new branch on GitHub. It includes error handling and retries for pushing to GitHub.

    Arguments:
        repo_dir: The local directory of the git repository
        commit_message: The commit message to use (default: "Added all accessibility features")
        remote_name: The name of the remote to push to (default: "origin")
    """
    # Stage and commit changes
    repo = Repo(repo_dir)
    with repo.config_writer() as cw:

        # Methods to ensure large repos work
        try:
            cw.set_value("http", "postBuffer", "524288000")
            cw.set_value("http", "version", "HTTP/1.1")
        except Exception:
            pass
        try:
            cw.set_value("core", "compression", "0")
            cw.set_value("pack", "windowMemory", "100m")
            cw.set_value("pack", "packSizeLimit", "100m")
        except Exception:
            pass
    new_branch = "accessibility-updates"
    origin = repo.remote(name=remote_name)

    # Delete remote branch if it already exists
    remote_branches = [ref.name.split('/')[-1] for ref in origin.refs]
    if new_branch in remote_branches:
        print(f"Deleting remote branch '{new_branch}'")
        origin.push(f":{new_branch}")  

    # Delete local branch if it already exists
    if new_branch in repo.heads:
        print(f"Deleting local branch '{new_branch}'")
        repo.git.branch('-D', new_branch)

    # (Re)Create the branch
    repo.git.checkout("-b", new_branch)

    # Stage and commit
    if repo.is_dirty(untracked_files=True):
        repo.git.add(".")
        repo.git.commit("-m", commit_message)
    else:
        print("No changes to commit")
        return False

    # Run gc to reduce pack sizes
    try:
        repo.git.gc('--aggressive', '--prune=now')
    except Exception:
        pass

    # Push branch to GitHub with retries/backoff
    push_success = False
    last_exc = None
    max_attempts = 4

    for attempt in range(1, max_attempts + 1):
        # Try to push
        try:
            push_result = origin.push(refspec=f"{new_branch}:{new_branch}", force=True)
            for info in push_result:
                print("Push summary:", info.summary, "\nFlags:", info.flags)
            push_success = True
            break

        # Exponential backoff
        except gitlib.GitCommandError as e:
            last_exc = e
            print(f"Push attempt {attempt} failed: {e}")
            time.sleep(attempt * 2)

    # Re-raise or print detailed error for upstream handling
    if not push_success:
        print("Push failed after retries.")
        if last_exc:
            
            raise last_exc
    
    # Return true on success
    return True



def create_release(repo_name, token, repo_dir="local_repo"):
    """
    Creates a release on GitHub created by stage_and_commit.
    It includes retries for handling GitHub server errors.

    Arguments:
        repo_name: The name of the GitHub repository (e.g., "username/repo")
        token: The GitHub access token for authentication
        repo_dir: The local directory of the git repository (default: "local_repo")
    """
    # Authenticate to GitHub and get repository
    auth = Auth.Token(token)
    g = Github(auth=auth)
    repo = g.get_repo(repo_name)

    # Zip the local repo directory and upload as a release asset
    try:
        timestamp = int(time.time())
        base_archive = os.path.join(tempfile.gettempdir(), f"{repo_name.replace('/', '_')}_{timestamp}")
        zip_path = shutil.make_archive(base_archive, 'zip', repo_dir)

        tag = f"auto-upload-{timestamp}"
        release = repo.create_git_release(tag=tag, name=f"Auto upload {timestamp}", message="Automated upload of modified repo", draft=True)
        
        failed = False
        try:
            try:
                
                # Upload using requests with retries and streaming
                upload_template = release.raw_data.get("upload_url")
                if not upload_template:
                    raise RuntimeError("release upload_url not found")
                upload_url = upload_template.split("{", 1)[0]
                params = {"name": os.path.basename(zip_path), "label": os.path.basename(zip_path)}

                session = requests.Session()
                if Retry is not None and HTTPAdapter is not None:
                    try:
                        retries = Retry(total=5, backoff_factor=1, status_forcelist=(500, 502, 503, 504))
                        adapter = HTTPAdapter(max_retries=retries)
                        session.mount("https://", adapter)
                        session.mount("http://", adapter)
                    except Exception:
                        pass

                headers = {
                    "Authorization": f"token {token}",
                    "Content-Type": "application/zip",
                    "Accept": "application/vnd.github.v3+json",
                }

                with open(zip_path, "rb") as fh:
                    try:
                        resp = session.post(upload_url, params=params, data=fh, headers=headers, timeout=(10, 1200))
                        resp.raise_for_status()
                        return resp.json()
                    finally:
                        session.close()

                print(f"Release asset uploaded: {release.html_url}")
                # Notify Electron UI about the release URL so it can open and display it
                try:
                    print(json.dumps({"action": "open_url", "url": release.html_url}), flush=True)
                except Exception:
                    pass
            except Exception:
                traceback.print_exc(file=sys.stderr)
                failed = True

            # If requests upload failed, try CLI as a fallback for large files
            if failed:
                if shutil.which("gh"):
                    try:
                        gh_cmd = ["gh", "release", "create", tag, zip_path, "--repo", repo_name, "--title", f"Auto upload {timestamp}", "--notes", "Automated upload", "--draft"]
                        proc = subprocess.run(gh_cmd, check=True, capture_output=True, text=True)
                        out = (proc.stdout or proc.stderr).strip()
                        if out:
                            print(out)
                        else:
                            print("gh release create succeeded")
                    except Exception:
                        traceback.print_exc(file=sys.stderr)
                else:
                    print("gh CLI not found; fallback unavailable")
        except Exception:
            traceback.print_exc(file=sys.stderr)

        # Clean up the local zip
        try:
            os.remove(zip_path)
        except Exception:
            pass

        return
    except Exception:
        traceback.print_exc(file=sys.stderr)
        raise


