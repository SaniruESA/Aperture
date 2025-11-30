# DEPENDENCIES REQUIRED: stuff for PyGithub, GitPython
from github import Github, Auth, GithubException
from git import Repo
import os
import time
import llama_code_edits

# NOT secure yet, have to manually add token.
TOKEN = ""

# # Authenticate a user with username and password
# # to allow them to create pull requests
# def login_auth(username: str, password: str):

#     # TODO: Add extra layers of auth/security?
#     auth = Auth.Login(username, password)
#     g = Github(auth=auth)
#     g.get_user().login

# # Authenticate a user with OAuth
# # to allow them to create pull requests
# def oauth(access_token: str):

#     # PUT THIs ON INFO LOG LTER
#     """
#     Quick guide to OAuth tokens with Github:
#     1) Log in to Github on browser/desktop app
#     2) On the top right of your screen, click "Settings"
#     3) Navigate to "Developer Settings" -> "Personal Access Tokens"
#     4) Click "Fine-Grained Tokens" and click "Generate New Token"
#     5) Customize the shown fields as you wish
#     6) Generate your token
#     7) Add the following permissions to the token:
        # -Repository:
        #     -Contents (Read/Write)
        #     -Metadata (Read)
        #     -Pull requests (Read/Write)
        # -Account
        #     -Profile (Read/Write)
#     """

#     auth = Auth.Token(access_token)
#     g = Github(auth=auth)
#     g.get_user().login

# Clone a Github repo, given the HTTPS URL and the directory to clone it into
def clone_repo(repo_url, clone_dir="local_repo"):

    # Delete a repo if it already exists
    if os.path.exists(clone_dir):
        print("Repo already exists, deleting...")

        import shutil
        shutil.rmtree(clone_dir)

    # Clone repo into the directory provided
    print(f"Cloning {repo_url}...")
    Repo.clone_from(repo_url, clone_dir)
    print("Clone complete")
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
        print(f"Remote branch '{new_branch}' exists, deleting...")
        origin.push(f":{new_branch}")  # delete remote branch
        print(f"Remote branch '{new_branch}' deleted.")

    # COMENT
    if new_branch in repo.heads:
        print(f"Local branch '{new_branch}' exists, deleting...")
        repo.git.branch('-D', new_branch)
        print(f"Local branch '{new_branch}' deleted.")


    # Create the branch if it doesn't exist
    # if new_branch in repo.heads:
    #     repo.git.checkout(new_branch)
    # else:
    repo.git.checkout("-b", new_branch)

    if repo.is_dirty(untracked_files=True):
        repo.git.add(".")
        repo.git.commit("-m", commit_message)
    else:
        print("No changes to commit.") # TODO: replace with info
        return False

    # Push branch to GitHub
    push_result = origin.push(refspec=f"{new_branch}:{new_branch}", force=True)
    for info in push_result:
        print("Push summary:", info.summary, "| flags:", info.flags)


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


# TODO:
# Make it so that when you clone a repo, and it already there, it properly deletes (currently it just has a PermissionError)
# Add functionality for this to use a seperate "accessibility" branch?
# info() logs stuff
# allow customizing the repo clone path