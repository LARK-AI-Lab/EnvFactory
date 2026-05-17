from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Union, Any
from mcp.server.fastmcp import FastMCP

# Section 1: Schema
class Commit(BaseModel):
    """Represents a Git commit."""
    hash: str = Field(..., description="The full SHA-1 hash uniquely identifying the commit")
    author: str = Field(..., description="The name and email of the commit author")
    date: str = Field(..., description="The timestamp when the commit was created")
    message: str = Field(..., description="The commit message describing the changes")

class Branch(BaseModel):
    """Represents a Git branch."""
    name: str = Field(..., description="The name of the branch")
    is_current: bool = Field(..., description="Whether this branch is currently checked out")
    sha: str = Field(..., description="The SHA-1 hash of the commit the branch points to")

class GitScenario(BaseModel):
    """Main scenario model for Git repository management."""
    repositories: Dict[str, dict] = Field(default={}, description="Repository data indexed by repo path")
    remoteUrlsMap: Dict[str, str] = Field(default={
        "origin": "https://github.com/user/repo.git",
        "upstream": "https://github.com/original/repo.git",
        "fork": "https://github.com/forked/repo.git",
        "backup": "https://backup.example.com/repo.git",
        "mirror": "https://mirror.example.com/repo.git",
        "dev": "https://dev.example.com/repo.git",
        "staging": "https://staging.example.com/repo.git",
        "production": "https://prod.example.com/repo.git",
        "local": "/path/to/local/repo.git",
        "test": "https://test.example.com/repo.git",
        "docs": "https://docs.example.com/repo.git",
        "ci": "https://ci.example.com/repo.git",
        "qa": "https://qa.example.com/repo.git",
        "uat": "https://uat.example.com/repo.git",
        "release": "https://release.example.com/repo.git",
        "beta": "https://beta.example.com/repo.git",
        "alpha": "https://alpha.example.com/repo.git",
        "nightly": "https://nightly.example.com/repo.git",
        "stable": "https://stable.example.com/repo.git",
        "legacy": "https://legacy.example.com/repo.git"
    }, description="Common remote repository URLs mapping")
    branchPrefixesMap: Dict[str, str] = Field(default={
        "feature": "feature/",
        "bugfix": "bugfix/",
        "hotfix": "hotfix/",
        "release": "release/",
        "chore": "chore/",
        "docs": "docs/",
        "refactor": "refactor/",
        "test": "test/",
        "style": "style/",
        "perf": "perf/",
        "ci": "ci/",
        "build": "build/",
        "revert": "revert/",
        "merge": "merge/",
        "wip": "wip/",
        "experimental": "experimental/",
        "prototype": "prototype/",
        "backup": "backup/",
        "archive": "archive/",
        "deprecated": "deprecated/",
        "legacy": "legacy/"
    }, description="Branch naming prefixes mapping")
    defaultBranchesMap: Dict[str, str] = Field(default={
        "GitHub": "main",
        "GitLab": "main",
        "Bitbucket": "master",
        "Azure": "master",
        "AWS CodeCommit": "master",
        "Google Cloud Source": "master",
        "default": "main",
        "legacy": "master",
        "old": "master",
        "modern": "main",
        "enterprise": "master",
        "open-source": "main",
        "community": "main",
        "corporate": "master",
        "startup": "main",
        "personal": "main",
        "fork": "main",
        "mirror": "main"
    }, description="Default branch names by platform")
    current_time: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", description="Current timestamp in ISO 8601 format")

Scenario_Schema = [Commit, Branch, GitScenario]

# Section 2: Class
class GitServer:
    def __init__(self):
        """Initialize Git server with empty state."""
        self.repositories: Dict[str, dict] = {}
        self.remoteUrlsMap: Dict[str, str] = {}
        self.branchPrefixesMap: Dict[str, str] = {}
        self.defaultBranchesMap: Dict[str, str] = {}
        self.current_time: str = ""

    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the Git server instance."""
        model = GitScenario(**scenario)
        self.repositories = model.repositories
        self.remoteUrlsMap = model.remoteUrlsMap
        self.branchPrefixesMap = model.branchPrefixesMap
        self.defaultBranchesMap = model.defaultBranchesMap
        self.current_time = model.current_time

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        return {
            "repositories": self.repositories,
            "remoteUrlsMap": self.remoteUrlsMap,
            "branchPrefixesMap": self.branchPrefixesMap,
            "defaultBranchesMap": self.defaultBranchesMap,
            "current_time": self.current_time
        }

    def _validate_repo_path(self, repo_path: str) -> None:
        """Validate repository path exists in loaded scenario."""
        if repo_path not in self.repositories:
            raise ValueError(f"Repository path does not exist in scenario: {repo_path}")

    def _get_repo_data(self, repo_path: str) -> dict:
        """Get repository data from scenario."""
        if repo_path in self.repositories:
            return self.repositories[repo_path]
        
        # Return empty structure if not found
        return {
            "commits": [],
            "branches": [],
            "current_branch": "",
            "remotes": {}
        }

    def git_status(self, repo_path: str) -> dict:
        """Show the working tree status of a Git repository."""
        self._validate_repo_path(repo_path)
        
        repo_data = self.repositories[repo_path]
        # Simulate status based on scenario data
        status_lines = []
        if "staged_files" in repo_data and repo_data["staged_files"]:
            for file in repo_data["staged_files"]:
                status_lines.append(f"A  {file}")  # Added to staging
        if "modified_files" in repo_data and repo_data["modified_files"]:
            for file in repo_data["modified_files"]:
                status_lines.append(f" M {file}")  # Modified
        if "untracked_files" in repo_data and repo_data["untracked_files"]:
            for file in repo_data["untracked_files"]:
                status_lines.append(f"?? {file}")  # Untracked
        
        branch = repo_data.get("current_branch", "main")
        status_output = f"## {branch}\n" + "\n".join(status_lines)
        return {"status_output": status_output}

    def git_log(self, repo_path: str, max_count: int = 10, start_timestamp: Optional[str] = None, end_timestamp: Optional[str] = None) -> dict:
        """Show the commit logs of a Git repository with optional filtering."""
        self._validate_repo_path(repo_path)
        
        repo_data = self.repositories[repo_path]
        commits = repo_data.get("commits", [])
        
        # Filter by count
        commits = commits[:max_count]
        
        # Filter by timestamp if provided
        if start_timestamp or end_timestamp:
            filtered_commits = []
            for commit in commits:
                commit_date = commit.get("date", "")
                if start_timestamp and commit_date < start_timestamp:
                    continue
                if end_timestamp and commit_date > end_timestamp:
                    continue
                filtered_commits.append(commit)
            commits = filtered_commits
        
        return {"commits": commits}

    def git_branch(self, repo_path: str, branch_type: str, contains: Optional[str] = None, not_contains: Optional[str] = None) -> dict:
        """List Git branches in a repository with optional filtering."""
        self._validate_repo_path(repo_path)
        
        repo_data = self.repositories[repo_path]
        branches = repo_data.get("branches", [])
        
        # Filter by branch type if specified
        if branch_type == "remote":
            branches = [b for b in branches if b["name"].startswith("origin/") or b["name"].startswith("upstream/")]
        elif branch_type == "local":
            branches = [b for b in branches if not (b["name"].startswith("origin/") or b["name"].startswith("upstream/"))]
        # branch_type == "all" means no filtering
        
        # Filter by contains/not_contains if specified
        if contains:
            branches = [b for b in branches if contains in b.get("sha", "")]
        if not_contains:
            branches = [b for b in branches if not_contains not in b.get("sha", "")]
        
        return {"branches": branches}

    def git_show(self, repo_path: str, revision: str, context_lines: int = 10) -> dict:
        """Show the contents and metadata of a specific commit or revision."""
        self._validate_repo_path(repo_path)
        
        repo_data = self.repositories[repo_path]
        commits = repo_data.get("commits", [])
        
        # Find commit by hash or branch name
        commit_content = None
        for commit in commits:
            if commit["hash"].startswith(revision) or revision in commit["message"]:
                commit_content = f"commit {commit['hash']}\nAuthor: {commit['author']}\nDate: {commit['date']}\n\n    {commit['message']}"
                break
        
        if commit_content is None:
            date_str = self.current_time.replace("T", " ")[:19]
            commit_content = f"commit {revision}\nAuthor: Unknown <unknown@example.com>\nDate: {date_str}\n\n    Default commit content for {revision}"
        
        return {"commit_content": commit_content}

    def git_diff_unstaged(self, repo_path: str, context_lines: int = 3) -> dict:
        """Show changes in the working directory that have not yet been staged."""
        self._validate_repo_path(repo_path)
        
        # Simulate diff for scenario data
        repo_data = self.repositories[repo_path]
        modified_files = repo_data.get("modified_files", [])
        
        diff_output = ""
        for file in modified_files:
            diff_output += f"diff --git a/{file} b/{file}\n"
            diff_output += f"--- a/{file}\n"
            diff_output += f"+++ b/{file}\n"
            diff_output += f"@@ -1,3 +1,3 @@\n"
            diff_output += f" line 1\n"
            diff_output += f"-old line 2\n"
            diff_output += f"+new line 2\n"
            diff_output += f" line 3\n\n"
        
        return {"diff_output": diff_output}

    def git_diff_staged(self, repo_path: str, context_lines: int = 3) -> dict:
        """Show changes that are currently staged and ready to be committed."""
        self._validate_repo_path(repo_path)
        
        # Simulate staged diff for scenario data
        repo_data = self.repositories[repo_path]
        staged_files = repo_data.get("staged_files", [])
        
        diff_output = ""
        for file in staged_files:
            diff_output += f"diff --git a/{file} b/{file}\n"
            diff_output += f"--- a/{file}\n"
            diff_output += f"+++ b/{file}\n"
            diff_output += f"@@ -1,3 +1,3 @@\n"
            diff_output += f" line 1\n"
            diff_output += f"-old line 2\n"
            diff_output += f"+new line 2\n"
            diff_output += f" line 3\n\n"
        
        return {"diff_output": diff_output}

    def git_diff(self, repo_path: str, target: str = "main", context_lines: int = 3) -> dict:
        """Show differences between the current working state and a target branch or commit."""
        self._validate_repo_path(repo_path)
        
        # Simulate diff for scenario data
        repo_data = self.repositories[repo_path]
        current_branch = repo_data.get("current_branch", "main")
        
        diff_output = f"diff --git a/current b/{target}\n"
        diff_output += f"Comparing {current_branch} with {target}\n"
        diff_output += f"Changes in working directory vs {target}\n"
        
        return {"diff_output": diff_output}

    def git_add(self, repo_path: str, files: List[str]) -> dict:
        """Add file contents to the staging area in preparation for commit."""
        self._validate_repo_path(repo_path)
        
        # Simulate adding files to staging in scenario data
        repo_data = self.repositories[repo_path]
        if "staged_files" not in repo_data:
            repo_data["staged_files"] = []
        
        for file in files:
            if file not in repo_data["staged_files"]:
                repo_data["staged_files"].append(file)
        
        return {"staged_files": files}

    def git_commit(self, repo_path: str, message: str) -> dict:
        """Record staged changes to the repository with a commit message."""
        self._validate_repo_path(repo_path)
        
        # Simulate commit in scenario data
        repo_data = self.repositories[repo_path]
        if "commits" not in repo_data:
            repo_data["commits"] = []
        
        commit_hash = f"simulated_{len(repo_data['commits']) + 1:07d}"
        date_str = self.current_time.replace("T", " ")[:19]
        commit = {
            "hash": commit_hash,
            "author": "Simulated User <user@example.com>",
            "date": date_str,
            "message": message
        }
        repo_data["commits"].insert(0, commit)
        
        # Clear staged files after commit
        if "staged_files" in repo_data:
            repo_data["staged_files"] = []
        
        return {"commit_hash": commit_hash, "message": message}

    def git_reset(self, repo_path: str) -> dict:
        """Unstage all currently staged changes, moving them back to the working directory."""
        self._validate_repo_path(repo_path)
        
        # Simulate reset in scenario data
        repo_data = self.repositories[repo_path]
        if "staged_files" in repo_data:
            repo_data["staged_files"] = []
        
        return {"status": "Successfully unstaged all changes"}

    def git_create_branch(self, repo_path: str, branch_name: str, base_branch: Optional[str] = None) -> dict:
        """Create a new branch in the repository, optionally from a specified base branch."""
        self._validate_repo_path(repo_path)
        
        # Simulate branch creation in scenario data
        repo_data = self.repositories[repo_path]
        if "branches" not in repo_data:
            repo_data["branches"] = []
        
        # Find base commit
        base_sha = "simulated_base_sha"
        if base_branch:
            for branch in repo_data.get("branches", []):
                if branch["name"] == base_branch:
                    base_sha = branch["sha"]
                    break
        
        new_branch = {
            "name": branch_name,
            "is_current": False,
            "sha": base_sha
        }
        repo_data["branches"].append(new_branch)
        
        actual_base = base_branch if base_branch else "HEAD"
        return {"branch_name": branch_name, "base_branch": actual_base}

    def git_checkout(self, repo_path: str, branch_name: str) -> dict:
        """Switch the working directory to a different branch."""
        self._validate_repo_path(repo_path)
        
        # Simulate checkout in scenario data
        repo_data = self.repositories[repo_path]
        if "branches" not in repo_data:
            repo_data["branches"] = []
        
        # Update current branch
        for branch in repo_data["branches"]:
            branch["is_current"] = (branch["name"] == branch_name)
        
        repo_data["current_branch"] = branch_name
        
        return {"current_branch": branch_name}

    def git_push(self, repo_path: str, remote: str = "origin", branch: Optional[str] = None, force: bool = False) -> dict:
        """Push local commits to a remote repository."""
        self._validate_repo_path(repo_path)
        
        # Simulate push in scenario data
        repo_data = self.repositories[repo_path]
        actual_branch = branch if branch else repo_data.get("current_branch", "main")
        return {"status": "Push successful", "remote": remote, "branch": actual_branch}

    def git_pull(self, repo_path: str, remote: str = "origin", branch: Optional[str] = None, rebase: bool = False) -> dict:
        """Fetch and integrate changes from a remote repository into the current branch."""
        self._validate_repo_path(repo_path)
        
        # Simulate pull in scenario data
        repo_data = self.repositories[repo_path]
        actual_branch = branch if branch else repo_data.get("current_branch", "main")
        return {
            "status": "Pull successful",
            "remote": remote,
            "branch": actual_branch,
            "updated_files": []
        }

# Section 3: MCP Tools
mcp = FastMCP(name="GitServer")
server = GitServer()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """Load scenario data into the Git server.
    
    Args:
        scenario (dict): Scenario dictionary matching GitScenario schema.
    
    Returns:
        success_message (str): Success message.
    """
    try:
        if not isinstance(scenario, dict):
            raise ValueError("Scenario must be a dictionary")
        server.load_scenario(scenario)
        return "Successfully loaded scenario"
    except Exception as e:
        raise e

@mcp.tool()
def save_scenario() -> dict:
    """Save current Git server state as scenario dictionary.
    
    Returns:
        scenario (dict): Dictionary containing all current state variables.
    """
    try:
        return server.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def git_status(repo_path: str) -> dict:
    """Show the working tree status of a Git repository.
    
    Args:
        repo_path (str): The absolute or relative filesystem path to the Git repository.
    
    Returns:
        status_output (str): The current status of the working directory.
    """
    try:
        if not repo_path or not isinstance(repo_path, str):
            raise ValueError("Repository path must be a non-empty string")
        return server.git_status(repo_path)
    except Exception as e:
        raise e

@mcp.tool()
def git_log(repo_path: str, max_count: int = 10, start_timestamp: Optional[str] = None, end_timestamp: Optional[str] = None) -> dict:
    """Show the commit logs of a Git repository with optional filtering.
    
    Args:
        repo_path (str): The absolute or relative filesystem path to the Git repository.
        max_count (int): [Optional] Maximum number of commits to retrieve. Defaults to 10.
        start_timestamp (str): [Optional] Start timestamp for filtering commits.
        end_timestamp (str): [Optional] End timestamp for filtering commits.
    
    Returns:
        commits (list): List of commit entries matching the specified criteria.
    """
    try:
        if not repo_path or not isinstance(repo_path, str):
            raise ValueError("Repository path must be a non-empty string")
        if not isinstance(max_count, int) or max_count <= 0:
            raise ValueError("max_count must be a positive integer")
        return server.git_log(repo_path, max_count, start_timestamp, end_timestamp)
    except Exception as e:
        raise e

@mcp.tool()
def git_branch(repo_path: str, branch_type: str, contains: Optional[str] = None, not_contains: Optional[str] = None) -> dict:
    """List Git branches in a repository with optional filtering.
    
    Args:
        repo_path (str): The absolute or relative filesystem path to the Git repository.
        branch_type (str): Type of branches to list ('local', 'remote', or 'all').
        contains (str): [Optional] Filter branches that contain the specified commit SHA.
        not_contains (str): [Optional] Filter branches that do NOT contain the specified commit SHA.
    
    Returns:
        branches (list): List of branches matching the specified criteria.
    """
    try:
        if not repo_path or not isinstance(repo_path, str):
            raise ValueError("Repository path must be a non-empty string")
        if branch_type not in ["local", "remote", "all"]:
            raise ValueError("branch_type must be one of: 'local', 'remote', 'all'")
        return server.git_branch(repo_path, branch_type, contains, not_contains)
    except Exception as e:
        raise e

@mcp.tool()
def git_show(repo_path: str, revision: str, context_lines: int = 10) -> dict:
    """Show the contents and metadata of a specific commit or revision.
    
    Args:
        repo_path (str): The absolute or relative filesystem path to the Git repository.
        revision (str): The revision to display (commit hash, branch name, tag, etc.).
        context_lines (int): [Optional] Number of surrounding context lines. Defaults to 10.
    
    Returns:
        commit_content (str): The full contents of the specified commit.
    """
    try:
        if not repo_path or not isinstance(repo_path, str):
            raise ValueError("Repository path must be a non-empty string")
        if not revision or not isinstance(revision, str):
            raise ValueError("Revision must be a non-empty string")
        return server.git_show(repo_path, revision, context_lines)
    except Exception as e:
        raise e

@mcp.tool()
def git_diff_unstaged(repo_path: str, context_lines: int = 3) -> dict:
    """Show changes in the working directory that have not yet been staged.
    
    Args:
        repo_path (str): The absolute or relative filesystem path to the Git repository.
        context_lines (int): [Optional] Number of surrounding context lines. Defaults to 3.
    
    Returns:
        diff_output (str): The unified diff output showing unstaged changes.
    """
    try:
        if not repo_path or not isinstance(repo_path, str):
            raise ValueError("Repository path must be a non-empty string")
        return server.git_diff_unstaged(repo_path, context_lines)
    except Exception as e:
        raise e

@mcp.tool()
def git_diff_staged(repo_path: str, context_lines: int = 3) -> dict:
    """Show changes that are currently staged and ready to be committed.
    
    Args:
        repo_path (str): The absolute or relative filesystem path to the Git repository.
        context_lines (int): [Optional] Number of surrounding context lines. Defaults to 3.
    
    Returns:
        diff_output (str): The unified diff output showing staged changes.
    """
    try:
        if not repo_path or not isinstance(repo_path, str):
            raise ValueError("Repository path must be a non-empty string")
        return server.git_diff_staged(repo_path, context_lines)
    except Exception as e:
        raise e

@mcp.tool()
def git_diff(repo_path: str, target: str = "main", context_lines: int = 3) -> dict:
    """Show differences between the current working state and a target branch or commit.
    
    Args:
        repo_path (str): The absolute or relative filesystem path to the Git repository.
        target (str): [Optional] Target branch name or commit hash. Defaults to 'main'.
        context_lines (int): [Optional] Number of surrounding context lines. Defaults to 3.
    
    Returns:
        diff_output (str): The unified diff output comparing current state with target.
    """
    try:
        if not repo_path or not isinstance(repo_path, str):
            raise ValueError("Repository path must be a non-empty string")
        return server.git_diff(repo_path, target, context_lines)
    except Exception as e:
        raise e

@mcp.tool()
def git_add(repo_path: str, files: List[str]) -> dict:
    """Add file contents to the staging area in preparation for commit.
    
    Args:
        repo_path (str): The absolute or relative filesystem path to the Git repository.
        files (list): List of file paths (relative to repository root) to stage.
    
    Returns:
        staged_files (list): List of file paths that were successfully staged.
    """
    try:
        if not repo_path or not isinstance(repo_path, str):
            raise ValueError("Repository path must be a non-empty string")
        if not files or not isinstance(files, list) or not all(isinstance(f, str) for f in files):
            raise ValueError("Files must be a non-empty list of strings")
        return server.git_add(repo_path, files)
    except Exception as e:
        raise e

@mcp.tool()
def git_commit(repo_path: str, message: str) -> dict:
    """Record staged changes to the repository with a commit message.
    
    Args:
        repo_path (str): The absolute or relative filesystem path to the Git repository.
        message (str): The commit message describing the changes.
    
    Returns:
        commit_hash (str): The SHA-1 hash of the newly created commit.
        message (str): The commit message that was recorded.
    """
    try:
        if not repo_path or not isinstance(repo_path, str):
            raise ValueError("Repository path must be a non-empty string")
        if not message or not isinstance(message, str):
            raise ValueError("Commit message must be a non-empty string")
        return server.git_commit(repo_path, message)
    except Exception as e:
        raise e

@mcp.tool()
def git_reset(repo_path: str) -> dict:
    """Unstage all currently staged changes, moving them back to the working directory.
    
    Args:
        repo_path (str): The absolute or relative filesystem path to the Git repository.
    
    Returns:
        status (str): The result status of the reset operation.
    """
    try:
        if not repo_path or not isinstance(repo_path, str):
            raise ValueError("Repository path must be a non-empty string")
        return server.git_reset(repo_path)
    except Exception as e:
        raise e

@mcp.tool()
def git_create_branch(repo_path: str, branch_name: str, base_branch: Optional[str] = None) -> dict:
    """Create a new branch in the repository, optionally from a specified base branch.
    
    Args:
        repo_path (str): The absolute or relative filesystem path to the Git repository.
        branch_name (str): The name for the new branch to be created.
        base_branch (str): [Optional] Existing branch or commit to use as starting point.
    
    Returns:
        branch_name (str): The name of the newly created branch.
        base_branch (str): The branch or commit the new branch was created from.
    """
    try:
        if not repo_path or not isinstance(repo_path, str):
            raise ValueError("Repository path must be a non-empty string")
        if not branch_name or not isinstance(branch_name, str):
            raise ValueError("Branch name must be a non-empty string")
        return server.git_create_branch(repo_path, branch_name, base_branch)
    except Exception as e:
        raise e

@mcp.tool()
def git_checkout(repo_path: str, branch_name: str) -> dict:
    """Switch the working directory to a different branch.
    
    Args:
        repo_path (str): The absolute or relative filesystem path to the Git repository.
        branch_name (str): The name of the branch to switch to.
    
    Returns:
        current_branch (str): The name of the branch that is now checked out.
    """
    try:
        if not repo_path or not isinstance(repo_path, str):
            raise ValueError("Repository path must be a non-empty string")
        if not branch_name or not isinstance(branch_name, str):
            raise ValueError("Branch name must be a non-empty string")
        return server.git_checkout(repo_path, branch_name)
    except Exception as e:
        raise e

@mcp.tool()
def git_push(repo_path: str, remote: str = "origin", branch: Optional[str] = None, force: bool = False) -> dict:
    """Push local commits to a remote repository.
    
    Args:
        repo_path (str): The absolute or relative filesystem path to the Git repository.
        remote (str): [Optional] Name of the remote repository. Defaults to 'origin'.
        branch (str): [Optional] Branch to push. Defaults to current branch.
        force (bool): [Optional] Whether to force push. Defaults to false.
    
    Returns:
        status (str): The result status of the push operation.
        remote (str): The name of the remote repository that was pushed to.
        branch (str): The name of the branch that was pushed.
    """
    try:
        if not repo_path or not isinstance(repo_path, str):
            raise ValueError("Repository path must be a non-empty string")
        if not isinstance(remote, str):
            raise ValueError("Remote must be a string")
        return server.git_push(repo_path, remote, branch, force)
    except Exception as e:
        raise e

@mcp.tool()
def git_pull(repo_path: str, remote: str = "origin", branch: Optional[str] = None, rebase: bool = False) -> dict:
    """Fetch and integrate changes from a remote repository into the current branch.
    
    Args:
        repo_path (str): The absolute or relative filesystem path to the Git repository.
        remote (str): [Optional] Name of the remote repository. Defaults to 'origin'.
        branch (str): [Optional] Remote branch to pull. Defaults to tracking branch.
        rebase (bool): [Optional] Whether to rebase instead of merge. Defaults to false.
    
    Returns:
        status (str): The result status of the pull operation.
        remote (str): The name of the remote repository that was pulled from.
        branch (str): The name of the branch that was pulled.
        updated_files (list): List of file paths that were updated.
    """
    try:
        if not repo_path or not isinstance(repo_path, str):
            raise ValueError("Repository path must be a non-empty string")
        if not isinstance(remote, str):
            raise ValueError("Remote must be a string")
        return server.git_pull(repo_path, remote, branch, rebase)
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()