# DEPENDENCIES REQUIRED: stuff for PyGithub, GitPython
from github import Github, Auth, GithubException
from git import Repo
import os
import time
import requests
import stat
import webbrowser
import pyperclip

CLIENT_ID = "Ov23liV0UHREdct0ILC3"

def authenticate_with_github():

    res = requests.post(
        "https://github.com/login/device/code",
        headers={"Accept": "application/json"},
        data={
            "client_id": CLIENT_ID,
            "scope": "repo read:user"
        }
    ).json()

    base_url = res["verification_uri"]
    code = res["user_code"]

    user_code = res["user_code"]
    pyperclip.copy(user_code)

    print("The GitHub authentication page will open shortly.")
    print("Your code has already been copied to your clipboard, you just need to paste it.")

    print(f"Code {user_code} copied to clipboard!")
    webbrowser.open(res["verification_uri"])

    device_code = res["device_code"]
    interval = res.get("interval", 5)

    while True:
        token_res = requests.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": CLIENT_ID,
                "device_code": device_code,
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code"
            }
        ).json()

        if "access_token" in token_res:
            return token_res["access_token"]

        if token_res.get("error") not in ("authorization_pending", "slow_down"):
            raise RuntimeError(token_res)

        time.sleep(interval)

# Error handler to delete read-only files
def remove_readonly(func, path, exc_info):
    os.chmod(path, stat.S_IWRITE)
    func(path)

# Clone a Github repo, given the HTTPS URL and the directory to clone it into
def clone_repo(repo_url, clone_dir="local_repo"):

    # Delete a repo if it already exists
    if os.path.exists(clone_dir):
        print("Local repo clone exists, deleting and replacing")

        import shutil
        shutil.rmtree(clone_dir, onexc=remove_readonly)

    # Clone repo into the directory provided
    Repo.clone_from(repo_url, clone_dir)
    print(f"Cloned {repo_url}")
    return clone_dir

# Stages all modified files and creates a commit.
def stage_and_commit(repo_dir, commit_message="Added all accessibility features", remote_name="origin") -> bool:

    # Stage and commit changes
    repo = Repo(repo_dir)
    new_branch = "accessibility-updates"
    origin = repo.remote(name=remote_name)

    # COMENT
    remote_branches = [ref.name.split('/')[-1] for ref in origin.refs]  # list of remote branch names
    if new_branch in remote_branches:
        print(f"Deleting remote branch '{new_branch}'")
        origin.push(f":{new_branch}")  # delete remote branch

    # COMENT
    if new_branch in repo.heads:
        print(f"Deleting local branch '{new_branch}'")
        repo.git.branch('-D', new_branch)

    repo.git.checkout("-b", new_branch)

    if repo.is_dirty(untracked_files=True):
        repo.git.add(".")
        repo.git.commit("-m", commit_message)
    else:
        print("No changes to commit") # TODO: replace with info()
        return False

    # Push branch to GitHub
    push_result = origin.push(refspec=f"{new_branch}:{new_branch}", force=True)
    for info in push_result:
        print("Push summary:", info.summary, "\nFlags:", info.flags)


    return True


# Create pull request
def create_pull_request(repo_name, branch_name, token, base_branch="main", repo_dir="local_repo"):

    # Get info about user and repo
    auth = Auth.Token(token)
    g = Github(auth=auth)
    test = g.get_user()
    repo = test.get_repo(repo_name)

    # Stage/commit changes
    result = stage_and_commit(repo_dir)

    # Cancel PR if no commited changes
    if not result:
        print("No commited changes; pull request canceled.") # TODO: info()
        return

    # Allow time for GitHub to process branch addition
    time.sleep(10)

    # TEST
    for b in repo.get_branches():
        print(b.name)


    # Retry PRs in case GitHub didn't process branch yet
    for i in range(3):
        try:
            # Create PR
            pr = repo.create_pull(
                title="Added all accessibility features",
                body="Automated PR to improve accessibility for the blind/deaf.",
                head=branch_name,
                base=base_branch
            )
            print(f"Pull request created: {pr.html_url}")
            return

        except GithubException as error:
            if error.status >= 500:
                print(f"GitHub 500 error, retrying in {i*2} seconds.")
                time.sleep(i)  # increasingly long backoff

            # Raise error if it wasn't 500
            else:
                raise
    raise Exception("GitHub failed too many times.")

