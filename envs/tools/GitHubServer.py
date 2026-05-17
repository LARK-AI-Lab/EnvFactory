from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP

# Section 1: Schema
class Repository(BaseModel):
    """Represents a GitHub repository."""
    owner: str = Field(..., description="Repository owner")
    repo: str = Field(..., description="Repository name")
    description: Optional[str] = Field(default=None, description="Repository description")
    stars: Optional[int] = Field(default=0, ge=0, description="Number of stars")
    private: Optional[bool] = Field(default=False, description="Whether repository is private")
    url: Optional[str] = Field(default=None, description="Repository URL")
    created_at: Optional[str] = Field(default=None, description="Creation timestamp")

class Issue(BaseModel):
    """Represents a GitHub issue."""
    issue_number: int = Field(..., ge=1, description="Issue number")
    title: str = Field(..., description="Issue title")
    body: Optional[str] = Field(default=None, description="Issue description")
    state: str = Field(default="open", description="Issue state")
    created_at: Optional[str] = Field(default=None, description="Creation timestamp")
    updated_at: Optional[str] = Field(default=None, description="Update timestamp")
    closed_at: Optional[str] = Field(default=None, description="Closing timestamp")

class PullRequest(BaseModel):
    """Represents a GitHub pull request."""
    pull_number: int = Field(..., ge=1, description="Pull request number")
    title: str = Field(..., description="PR title")
    body: Optional[str] = Field(default=None, description="PR description")
    state: str = Field(default="open", description="PR state")
    head: Optional[str] = Field(default=None, description="Source branch")
    base: Optional[str] = Field(default=None, description="Target branch")
    created_at: Optional[str] = Field(default=None, description="Creation timestamp")
    updated_at: Optional[str] = Field(default=None, description="Update timestamp")
    merged: Optional[bool] = Field(default=False, description="Whether PR is merged")
    merge_commit_sha: Optional[str] = Field(default=None, description="Merge commit SHA")

class Branch(BaseModel):
    """Represents a GitHub branch."""
    name: str = Field(..., description="Branch name")
    sha: Optional[str] = Field(default=None, description="Branch SHA")
    protected: Optional[bool] = Field(default=False, description="Whether branch is protected")

class Commit(BaseModel):
    """Represents a GitHub commit."""
    sha: str = Field(..., description="Commit SHA")
    message: str = Field(..., description="Commit message")
    author: Optional[str] = Field(default=None, description="Commit author")
    date: Optional[str] = Field(default=None, description="Commit date")

class FileContent(BaseModel):
    """Represents file content from GitHub."""
    path: str = Field(..., description="File path")
    content: Optional[str] = Field(default=None, description="File content")
    encoding: Optional[str] = Field(default=None, description="Content encoding")
    size: Optional[int] = Field(default=0, ge=0, description="File size in bytes")

class GitHubScenario(BaseModel):
    """Main scenario model for GitHub API operations."""
    repositories: Dict[str, Repository] = Field(default={}, description="Repository storage")
    issues: Dict[str, Dict[int, Issue]] = Field(default={}, description="Issues by repo")
    pull_requests: Dict[str, Dict[int, PullRequest]] = Field(default={}, description="PRs by repo")
    branches: Dict[str, Dict[str, Branch]] = Field(default={}, description="Branches by repo")
    commits: Dict[str, List[Commit]] = Field(default={}, description="Commits by repo")
    files: Dict[str, Dict[str, FileContent]] = Field(default={}, description="Files by repo")
    current_user: Optional[Dict[str, str]] = Field(default=None, description="Current user info")
    next_issue_number: Dict[str, int] = Field(default={}, description="Next issue number by repo")
    next_pr_number: Dict[str, int] = Field(default={}, description="Next PR number by repo")
    current_time: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", description="Current timestamp in ISO 8601 format")

Scenario_Schema = [Repository, Issue, PullRequest, Branch, Commit, FileContent, GitHubScenario]

# Section 2: Class
class GitHubServer:
    def __init__(self):
        """Initialize GitHub server with empty state."""
        self.repositories: Dict[str, Repository] = {}
        self.issues: Dict[str, Dict[int, Issue]] = {}
        self.pull_requests: Dict[str, Dict[int, PullRequest]] = {}
        self.branches: Dict[str, Dict[str, Branch]] = {}
        self.commits: Dict[str, List[Commit]] = {}
        self.files: Dict[str, Dict[str, FileContent]] = {}
        self.current_user: Optional[Dict[str, str]] = None
        self.next_issue_number: Dict[str, int] = {}
        self.next_pr_number: Dict[str, int] = {}
        self.current_time: str = ""

    @staticmethod
    def _normalize_scenario_keys(scenario: dict) -> dict:
        """Normalize scenario dictionary keys for comparison (convert int keys to strings for issues and pull_requests)."""
        normalized = scenario.copy()
        if "issues" in normalized:
            normalized["issues"] = {
                repo_key: {
                    str(issue_num): issue_data
                    for issue_num, issue_data in repo_issues.items()
                }
                for repo_key, repo_issues in normalized["issues"].items()
            }
        if "pull_requests" in normalized:
            normalized["pull_requests"] = {
                repo_key: {
                    str(pr_num): pr_data
                    for pr_num, pr_data in repo_prs.items()
                }
                for repo_key, repo_prs in normalized["pull_requests"].items()
            }
        return normalized

    def load_scenario(self, scenario: dict) -> None:
        """Load scenario data into the server instance."""
        # Convert string keys to int for issues and pull_requests (JSON serialization converts int keys to strings)
        # Handle both int and string keys for compatibility
        processed_scenario = scenario.copy()
        if "issues" in processed_scenario:
            processed_scenario["issues"] = {
                repo_key: {
                    int(issue_num): issue_data
                    for issue_num, issue_data in repo_issues.items()
                }
                for repo_key, repo_issues in processed_scenario["issues"].items()
            }
        if "pull_requests" in processed_scenario:
            processed_scenario["pull_requests"] = {
                repo_key: {
                    int(pr_num): pr_data
                    for pr_num, pr_data in repo_prs.items()
                }
                for repo_key, repo_prs in processed_scenario["pull_requests"].items()
            }
        model = GitHubScenario(**processed_scenario)
        self.repositories = model.repositories
        self.issues = model.issues
        self.pull_requests = model.pull_requests
        self.branches = model.branches
        self.commits = model.commits
        self.files = model.files
        self.current_user = model.current_user
        self.next_issue_number = model.next_issue_number
        self.next_pr_number = model.next_pr_number
        self.current_time = model.current_time

    def save_scenario(self) -> dict:
        """Save current state as scenario dictionary."""
        # Convert int keys to strings for issues and pull_requests to ensure JSON serialization consistency
        return {
            "repositories": {k: v.model_dump() for k, v in self.repositories.items()},
            "issues": {k: {str(ik): iv.model_dump() for ik, iv in v.items()} for k, v in self.issues.items()},
            "pull_requests": {k: {str(ik): iv.model_dump() for ik, iv in v.items()} for k, v in self.pull_requests.items()},
            "branches": {k: {ik: iv.model_dump() for ik, iv in v.items()} for k, v in self.branches.items()},
            "commits": {k: [c.model_dump() for c in v] for k, v in self.commits.items()},
            "files": {k: {ik: iv.model_dump() for ik, iv in v.items()} for k, v in self.files.items()},
            "current_user": self.current_user,
            "next_issue_number": self.next_issue_number,
            "next_pr_number": self.next_pr_number,
            "current_time": self.current_time
        }

    def search_repositories(self, q: str, sort: Optional[str] = None, order: Optional[str] = None, per_page: Optional[str] = None, page: Optional[int] = None) -> dict:
        """Search for GitHub repositories."""
        results = []
        for repo_key, repo in self.repositories.items():
            if q.lower() in repo.repo.lower() or q.lower() in (repo.description or "").lower():
                results.append({
                    "owner": repo.owner,
                    "repo": repo.repo,
                    "description": repo.description,
                    "stars": repo.stars
                })
        return {"repositories": results}

    def create_repository(self, name: str, description: Optional[str] = None, private: Optional[bool] = None, autoInit: Optional[str] = None) -> dict:
        """Create a new GitHub repository."""
        repo_key = f"{self.current_user['username']}/{name}"
        repo = Repository(
            owner=self.current_user['username'],
            repo=name,
            description=description,
            private=private or False,
            url=f"https://github.com/{repo_key}",
            created_at=self.current_time
        )
        self.repositories[repo_key] = repo
        self.issues[repo_key] = {}
        self.pull_requests[repo_key] = {}
        self.branches[repo_key] = {"main": Branch(name="main")}
        self.commits[repo_key] = []
        self.files[repo_key] = {}
        self.next_issue_number[repo_key] = 1
        self.next_pr_number[repo_key] = 1
        return {
            "owner": repo.owner,
            "repo": repo.repo,
            "url": repo.url,
            "created_at": repo.created_at
        }

    def delete_repository(self, owner: str, repo: str) -> dict:
        """Delete a GitHub repository."""
        repo_key = f"{owner}/{repo}"
        deleted = False
        if repo_key in self.repositories:
            del self.repositories[repo_key]
            if repo_key in self.issues:
                del self.issues[repo_key]
            if repo_key in self.pull_requests:
                del self.pull_requests[repo_key]
            if repo_key in self.branches:
                del self.branches[repo_key]
            if repo_key in self.commits:
                del self.commits[repo_key]
            if repo_key in self.files:
                del self.files[repo_key]
            if repo_key in self.next_issue_number:
                del self.next_issue_number[repo_key]
            if repo_key in self.next_pr_number:
                del self.next_pr_number[repo_key]
            deleted = True
        return {"owner": owner, "repo": repo, "deleted": deleted}

    def get_file_contents(self, owner: str, repo: str, path: str, branch: Optional[str] = None) -> dict:
        """Get file or directory contents from a GitHub repository."""
        repo_key = f"{owner}/{repo}"
        if repo_key in self.files and path in self.files[repo_key]:
            file_data = self.files[repo_key][path]
            return {
                "path": file_data.path,
                "content": file_data.content,
                "encoding": file_data.encoding,
                "size": file_data.size
            }
        return {"path": path, "content": None, "encoding": None, "size": 0}

    def create_file(self, owner: str, repo: str, path: str, content: str, message: str, branch: str) -> dict:
        """Create a new file in a GitHub repository."""
        repo_key = f"{owner}/{repo}"
        file_data = FileContent(
            path=path,
            content=content,
            encoding="utf-8",
            size=len(content.encode('utf-8'))
        )
        if repo_key not in self.files:
            self.files[repo_key] = {}
        self.files[repo_key][path] = file_data
        timestamp_str = self.current_time.replace(":", "").replace("-", "").replace("T", "_")[:15]
        commit_sha = f"create_{path.replace('/', '_')}_{timestamp_str}"
        return {
            "commit_sha": commit_sha,
            "file_sha": f"file_{path.replace('/', '_')}",
            "path": path
        }

    def delete_file(self, owner: str, repo: str, path: str, message: str, branch: str, sha: str) -> dict:
        """Delete a file from a GitHub repository."""
        repo_key = f"{owner}/{repo}"
        if repo_key in self.files and path in self.files[repo_key]:
            del self.files[repo_key][path]
        timestamp_str = self.current_time.replace(":", "").replace("-", "").replace("T", "_")[:15]
        commit_sha = f"delete_{path.replace('/', '_')}_{timestamp_str}"
        return {
            "commit_sha": commit_sha,
            "path": path,
            "deleted": True
        }

    def push_files(self, owner: str, repo: str, branch: str, files: List[dict], message: str) -> dict:
        """Push multiple files to a GitHub repository in a single commit."""
        repo_key = f"{owner}/{repo}"
        if repo_key not in self.files:
            self.files[repo_key] = {}
        for file_data in files:
            path = file_data.get("path")
            content = file_data.get("content")
            if path and content:
                self.files[repo_key][path] = FileContent(
                    path=path,
                    content=content,
                    encoding="utf-8",
                    size=len(content.encode('utf-8'))
                )
        timestamp_str = self.current_time.replace(":", "").replace("-", "").replace("T", "_")[:15]
        commit_sha = f"push_{len(files)}_{timestamp_str}"
        return {
            "commit_sha": commit_sha,
            "files_changed": len(files),
            "branch": branch
        }

    def create_issue(self, owner: str, repo: str, title: str, body: Optional[str] = None, assignees: Optional[str] = None, labels: Optional[str] = None, milestone: Optional[str] = None) -> dict:
        """Create a new issue in a GitHub repository."""
        repo_key = f"{owner}/{repo}"
        issue_number = self.next_issue_number.get(repo_key, 1)
        issue = Issue(
            issue_number=issue_number,
            title=title,
            body=body,
            state="open",
            created_at=self.current_time
        )
        if repo_key not in self.issues:
            self.issues[repo_key] = {}
        self.issues[repo_key][issue_number] = issue
        self.next_issue_number[repo_key] = issue_number + 1
        return {
            "issue_number": issue_number,
            "title": title,
            "state": "open",
            "created_at": issue.created_at
        }

    def create_pull_request(self, owner: str, repo: str, title: str, head: str, base: str, body: Optional[str] = None, draft: Optional[str] = None, maintainer_can_modify: Optional[str] = None) -> dict:
        """Create a new pull request in a GitHub repository."""
        repo_key = f"{owner}/{repo}"
        pr_number = self.next_pr_number.get(repo_key, 1)
        pr = PullRequest(
            pull_number=pr_number,
            title=title,
            body=body,
            state="open",
            head=head,
            base=base,
            created_at=self.current_time
        )
        if repo_key not in self.pull_requests:
            self.pull_requests[repo_key] = {}
        self.pull_requests[repo_key][pr_number] = pr
        self.next_pr_number[repo_key] = pr_number + 1
        return {
            "pull_number": pr_number,
            "title": title,
            "state": "open",
            "created_at": pr.created_at
        }

    def fork_repository(self, owner: str, repo: str, organization: Optional[str] = None) -> dict:
        """Fork a GitHub repository to your account or specified organization."""
        repo_key = f"{owner}/{repo}"
        fork_owner = organization or self.current_user['username']
        fork_key = f"{fork_owner}/{repo}"
        if repo_key in self.repositories:
            original = self.repositories[repo_key]
            fork_repo = Repository(
                owner=fork_owner,
                repo=repo,
                description=original.description,
                private=False,
                url=f"https://github.com/{fork_key}",
                created_at=self.current_time
            )
            self.repositories[fork_key] = fork_repo
            self.issues[fork_key] = {}
            self.pull_requests[fork_key] = {}
            self.branches[fork_key] = {"main": Branch(name="main")}
            self.commits[fork_key] = []
            self.files[fork_key] = {}
            self.next_issue_number[fork_key] = 1
            self.next_pr_number[fork_key] = 1
        return {
            "owner": fork_owner,
            "repo": repo,
            "forked_from": repo_key,
            "created_at": self.current_time
        }

    def create_branch(self, owner: str, repo: str, branch: str, from_branch: Optional[str] = None) -> dict:
        """Create a new branch in a GitHub repository."""
        repo_key = f"{owner}/{repo}"
        new_branch = Branch(
            name=branch,
            sha=f"branch_{branch}_{self.current_time.replace(':', '').replace('-', '').replace('T', '_')[:15]}"
        )
        if repo_key not in self.branches:
            self.branches[repo_key] = {}
        self.branches[repo_key][branch] = new_branch
        created_at = self.current_time
        return {
            "branch": branch,
            "sha": new_branch.sha,
            "created_at": created_at
        }

    def list_branches(self, owner: str, repo: str, per_page: Optional[int] = None, page: Optional[int] = None) -> dict:
        """List branches in a GitHub repository."""
        repo_key = f"{owner}/{repo}"
        branches = []
        if repo_key in self.branches:
            for branch_name, branch_data in self.branches[repo_key].items():
                branches.append({
                    "name": branch_data.name,
                    "sha": branch_data.sha,
                    "protected": branch_data.protected
                })
        return {"branches": branches}

    def list_commits(self, owner: str, repo: str, page: Optional[int] = None, per_page: Optional[str] = None, sha: Optional[str] = None, path: Optional[str] = None, author: Optional[str] = None, since: Optional[str] = None, until: Optional[str] = None) -> dict:
        """Get list of commits for a GitHub repository branch."""
        repo_key = f"{owner}/{repo}"
        commits = []
        if repo_key in self.commits:
            for commit in self.commits[repo_key]:
                commits.append({
                    "sha": commit.sha,
                    "message": commit.message,
                    "author": commit.author,
                    "date": commit.date
                })
        return {"commits": commits}

    def list_issues(self, owner: str, repo: str, state: Optional[str] = None, labels: Optional[str] = None, sort: Optional[str] = None, direction: Optional[str] = None, since: Optional[str] = None, page: Optional[int] = None, per_page: Optional[str] = None) -> dict:
        """List issues in a GitHub repository with filtering options."""
        repo_key = f"{owner}/{repo}"
        issues = []
        if repo_key in self.issues:
            for issue_data in self.issues[repo_key].values():
                if state and issue_data.state != state:
                    continue
                issues.append({
                    "issue_number": issue_data.issue_number,
                    "title": issue_data.title,
                    "state": issue_data.state,
                    "created_at": issue_data.created_at
                })
        return {"issues": issues}

    def update_issue(self, owner: str, repo: str, issue_number: int, title: Optional[str] = None, body: Optional[str] = None, state: Optional[str] = None, labels: Optional[str] = None, assignees: Optional[str] = None, milestone: Optional[str] = None) -> dict:
        """Update an existing issue in a GitHub repository."""
        repo_key = f"{owner}/{repo}"
        if repo_key in self.issues and issue_number in self.issues[repo_key]:
            issue = self.issues[repo_key][issue_number]
            if title:
                issue.title = title
            if body:
                issue.body = body
            if state:
                issue.state = state
                if state == "closed":
                    issue.closed_at = self.current_time
            issue.updated_at = self.current_time
            return {
                "issue_number": issue_number,
                "title": issue.title,
                "state": issue.state,
                "updated_at": issue.updated_at
            }
        return {"issue_number": issue_number, "title": "", "state": "", "updated_at": ""}

    def add_issue_comment(self, owner: str, repo: str, issue_number: int, body: str) -> dict:
        """Add a comment to an existing issue."""
        return {
            "comment_id": hash(f"{owner}/{repo}/{issue_number}/{body}") % 1000000,
            "issue_number": issue_number,
            "created_at": self.current_time
        }

    def close_issue(self, owner: str, repo: str, issue_number: int) -> dict:
        """Close an existing issue in a GitHub repository."""
        repo_key = f"{owner}/{repo}"
        if repo_key in self.issues and issue_number in self.issues[repo_key]:
            issue = self.issues[repo_key][issue_number]
            issue.state = "closed"
            issue.closed_at = self.current_time
            return {
                "issue_number": issue_number,
                "title": issue.title,
                "state": issue.state,
                "closed_at": issue.closed_at
            }
        return {"issue_number": issue_number, "title": "", "state": "closed", "closed_at": self.current_time}

    def search_code(self, q: str, sort: Optional[str] = None, order: Optional[str] = None, per_page: Optional[str] = None, page: Optional[int] = None) -> dict:
        """Search for code in GitHub repositories."""
        return {"results": []}

    def search_issues(self, q: str, sort: Optional[str] = None, order: Optional[str] = None, per_page: Optional[str] = None, page: Optional[int] = None) -> dict:
        """Search for issues and pull requests in GitHub repositories."""
        issues = []
        for repo_key, repo_issues in self.issues.items():
            owner, repo = repo_key.split("/")
            for issue_data in repo_issues.values():
                if q.lower() in issue_data.title.lower():
                    issues.append({
                        "owner": owner,
                        "repo": repo,
                        "issue_number": issue_data.issue_number,
                        "title": issue_data.title,
                        "state": issue_data.state
                    })
        for repo_key, repo_prs in self.pull_requests.items():
            owner, repo = repo_key.split("/")
            for pr_data in repo_prs.values():
                if q.lower() in pr_data.title.lower():
                    issues.append({
                        "owner": owner,
                        "repo": repo,
                        "issue_number": pr_data.pull_number,
                        "title": pr_data.title,
                        "state": pr_data.state
                    })
        return {"issues": issues}

    def search_users(self, q: str, sort: Optional[str] = None, order: Optional[str] = None, per_page: Optional[str] = None, page: Optional[int] = None) -> dict:
        """Search for users on GitHub."""
        return {"users": []}

    def get_issue(self, owner: str, repo: str, issue_number: int) -> dict:
        """Get detailed information for a specific issue."""
        repo_key = f"{owner}/{repo}"
        if repo_key in self.issues and issue_number in self.issues[repo_key]:
            issue = self.issues[repo_key][issue_number]
            return {
                "issue_number": issue.issue_number,
                "title": issue.title,
                "body": issue.body,
                "state": issue.state,
                "created_at": issue.created_at,
                "updated_at": issue.updated_at
            }
        return {"issue_number": issue_number, "title": "", "body": "", "state": "", "created_at": "", "updated_at": ""}

    def get_pull_request(self, owner: str, repo: str, pull_number: int) -> dict:
        """Get detailed information for a specific pull request."""
        repo_key = f"{owner}/{repo}"
        if repo_key in self.pull_requests and pull_number in self.pull_requests[repo_key]:
            pr = self.pull_requests[repo_key][pull_number]
            return {
                "pull_number": pr.pull_number,
                "title": pr.title,
                "body": pr.body,
                "state": pr.state,
                "created_at": pr.created_at,
                "updated_at": pr.updated_at
            }
        return {"pull_number": pull_number, "title": "", "body": "", "state": "", "created_at": "", "updated_at": ""}

    def list_pull_requests(self, owner: str, repo: str, state: Optional[str] = None, head: Optional[str] = None, base: Optional[str] = None, sort: Optional[str] = None, direction: Optional[str] = None, per_page: Optional[str] = None, page: Optional[int] = None) -> dict:
        """List and filter pull requests in a repository."""
        repo_key = f"{owner}/{repo}"
        prs = []
        if repo_key in self.pull_requests:
            for pr_data in self.pull_requests[repo_key].values():
                if state and pr_data.state != state:
                    continue
                if head and pr_data.head != head:
                    continue
                if base and pr_data.base != base:
                    continue
                prs.append({
                    "pull_number": pr_data.pull_number,
                    "title": pr_data.title,
                    "state": pr_data.state,
                    "created_at": pr_data.created_at
                })
        return {"pull_requests": prs}

    def create_pull_request_review(self, owner: str, repo: str, pull_number: int, body: str, event: str, commit_id: Optional[str] = None, comments: Optional[str] = None) -> dict:
        """Create a review for a pull request."""
        return {
            "review_id": hash(f"{owner}/{repo}/{pull_number}/{body}") % 1000000,
            "pull_number": pull_number,
            "state": event,
            "submitted_at": self.current_time
        }

    def merge_pull_request(self, owner: str, repo: str, pull_number: int, commit_title: Optional[str] = None, commit_message: Optional[str] = None, merge_method: Optional[str] = None) -> dict:
        """Merge a pull request."""
        repo_key = f"{owner}/{repo}"
        if repo_key in self.pull_requests and pull_number in self.pull_requests[repo_key]:
            pr = self.pull_requests[repo_key][pull_number]
            pr.state = "merged"
            pr.merged = True
            timestamp_str = self.current_time.replace(":", "").replace("-", "").replace("T", "_")[:15]
            pr.merge_commit_sha = f"merge_{pull_number}_{timestamp_str}"
            return {
                "pull_number": pull_number,
                "merged": True,
                "merge_commit_sha": pr.merge_commit_sha
            }
        return {"pull_number": pull_number, "merged": False, "merge_commit_sha": ""}

    def get_pull_request_files(self, owner: str, repo: str, pull_number: int) -> dict:
        """Get list of files changed in a pull request."""
        return {"files": []}

    def get_pull_request_status(self, owner: str, repo: str, pull_number: int) -> dict:
        """Get comprehensive status of all status checks for a pull request."""
        return {
            "pull_number": pull_number,
            "state": "success",
            "statuses": []
        }

    def update_pull_request_branch(self, owner: str, repo: str, pull_number: int, expected_head_sha: Optional[str] = None) -> dict:
        """Update pull request branch with latest changes from base branch."""
        return {
            "pull_number": pull_number,
            "updated": True,
            "message": "Branch updated successfully"
        }

    def get_pull_request_comments(self, owner: str, repo: str, pull_number: int) -> dict:
        """Get review comments for a pull request."""
        return {"comments": []}

    def get_pull_request_reviews(self, owner: str, repo: str, pull_number: int) -> dict:
        """Get reviews for a pull request."""
        return {"reviews": []}

    def list_user_repositories(self, type: Optional[str] = None, sort: Optional[str] = None, direction: Optional[str] = None, per_page: Optional[str] = None, page: Optional[int] = None) -> dict:
        """List repositories for the current user."""
        repos = []
        for repo_key, repo in self.repositories.items():
            if repo.owner == self.current_user['username']:
                repos.append({
                    "owner": repo.owner,
                    "repo": repo.repo,
                    "description": repo.description,
                    "private": repo.private
                })
        return {"repositories": repos}

    def get_github_user_info(self) -> dict:
        """Get GitHub user information for the current authenticated user."""
        return self.current_user or {}

# Section 3: MCP Tools
mcp = FastMCP(name="GitHubServer")
server = GitHubServer()

@mcp.tool()
def load_scenario(scenario: dict) -> str:
    """Load scenario data into the GitHub server."""
    try:
        if not isinstance(scenario, dict):
            raise ValueError("Scenario must be a dictionary")
        server.load_scenario(scenario)
        return "Successfully loaded scenario"
    except Exception as e:
        raise e

@mcp.tool()
def save_scenario() -> dict:
    """Save current GitHub state as scenario dictionary."""
    try:
        return server.save_scenario()
    except Exception as e:
        raise e

@mcp.tool()
def search_repositories(q: str, sort: Optional[str] = None, order: Optional[str] = None, per_page: Optional[str] = None, page: Optional[int] = None) -> dict:
    """Search for GitHub repositories using GitHub repository search syntax."""
    try:
        if not q or not isinstance(q, str):
            raise ValueError("Query must be a non-empty string")
        return server.search_repositories(q, sort, order, per_page, page)
    except Exception as e:
        raise e

@mcp.tool()
def create_repository(name: str, description: Optional[str] = None, private: Optional[bool] = None, autoInit: Optional[str] = None) -> dict:
    """Create a new GitHub repository in your account."""
    try:
        if not name or not isinstance(name, str):
            raise ValueError("Repository name must be a non-empty string")
        return server.create_repository(name, description, private, autoInit)
    except Exception as e:
        raise e

@mcp.tool()
def delete_repository(owner: str, repo: str) -> dict:
    """Delete a GitHub repository."""
    try:
        if not owner or not repo:
            raise ValueError("Owner and repository name are required")
        return server.delete_repository(owner, repo)
    except Exception as e:
        raise e

@mcp.tool()
def get_file_contents(owner: str, repo: str, path: str, branch: Optional[str] = None) -> dict:
    """Get file or directory contents from a GitHub repository."""
    try:
        if not owner or not repo or not path:
            raise ValueError("Owner, repository, and path are required")
        return server.get_file_contents(owner, repo, path, branch)
    except Exception as e:
        raise e

@mcp.tool()
def create_file(owner: str, repo: str, path: str, content: str, message: str, branch: str) -> dict:
    """Create a new file in a GitHub repository with specified content and commit message."""
    try:
        if not owner or not repo or not path or not content or not message or not branch:
            raise ValueError("All parameters are required")
        return server.create_file(owner, repo, path, content, message, branch)
    except Exception as e:
        raise e

@mcp.tool()
def delete_file(owner: str, repo: str, path: str, message: str, branch: str, sha: str) -> dict:
    """Delete a file from a GitHub repository."""
    try:
        if not owner or not repo or not path or not message or not branch or not sha:
            raise ValueError("All parameters are required")
        return server.delete_file(owner, repo, path, message, branch, sha)
    except Exception as e:
        raise e

@mcp.tool()
def push_files(owner: str, repo: str, branch: str, files: List[dict], message: str) -> dict:
    """Push multiple files to a GitHub repository in a single commit."""
    try:
        if not owner or not repo or not branch or not files or not message:
            raise ValueError("All parameters are required")
        return server.push_files(owner, repo, branch, files, message)
    except Exception as e:
        raise e

@mcp.tool()
def create_issue(owner: str, repo: str, title: str, body: Optional[str] = None, assignees: Optional[str] = None, labels: Optional[str] = None, milestone: Optional[str] = None) -> dict:
    """Create a new issue in a GitHub repository."""
    try:
        if not owner or not repo or not title:
            raise ValueError("Owner, repository, and title are required")
        return server.create_issue(owner, repo, title, body, assignees, labels, milestone)
    except Exception as e:
        raise e

@mcp.tool()
def create_pull_request(owner: str, repo: str, title: str, head: str, base: str, body: Optional[str] = None, draft: Optional[str] = None, maintainer_can_modify: Optional[str] = None) -> dict:
    """Create a new pull request in a GitHub repository."""
    try:
        if not owner or not repo or not title or not head or not base:
            raise ValueError("Owner, repository, title, head, and base are required")
        return server.create_pull_request(owner, repo, title, head, base, body, draft, maintainer_can_modify)
    except Exception as e:
        raise e

@mcp.tool()
def fork_repository(owner: str, repo: str, organization: Optional[str] = None) -> dict:
    """Fork a GitHub repository to your account or specified organization."""
    try:
        if not owner or not repo:
            raise ValueError("Owner and repository name are required")
        return server.fork_repository(owner, repo, organization)
    except Exception as e:
        raise e

@mcp.tool()
def create_branch(owner: str, repo: str, branch: str, from_branch: Optional[str] = None) -> dict:
    """Create a new branch in a GitHub repository."""
    try:
        if not owner or not repo or not branch:
            raise ValueError("Owner, repository, and branch name are required")
        return server.create_branch(owner, repo, branch, from_branch)
    except Exception as e:
        raise e

@mcp.tool()
def list_branches(owner: str, repo: str, per_page: Optional[int] = None, page: Optional[int] = None) -> dict:
    """List branches in a GitHub repository."""
    try:
        if not owner or not repo:
            raise ValueError("Owner and repository name are required")
        return server.list_branches(owner, repo, per_page, page)
    except Exception as e:
        raise e

@mcp.tool()
def list_commits(owner: str, repo: str, page: Optional[int] = None, per_page: Optional[str] = None, sha: Optional[str] = None, path: Optional[str] = None, author: Optional[str] = None, since: Optional[str] = None, until: Optional[str] = None) -> dict:
    """Get list of commits for a GitHub repository branch."""
    try:
        if not owner or not repo:
            raise ValueError("Owner and repository name are required")
        return server.list_commits(owner, repo, page, per_page, sha, path, author, since, until)
    except Exception as e:
        raise e

@mcp.tool()
def list_issues(owner: str, repo: str, state: Optional[str] = None, labels: Optional[str] = None, sort: Optional[str] = None, direction: Optional[str] = None, since: Optional[str] = None, page: Optional[int] = None, per_page: Optional[str] = None) -> dict:
    """List issues in a GitHub repository with filtering options."""
    try:
        if not owner or not repo:
            raise ValueError("Owner and repository name are required")
        return server.list_issues(owner, repo, state, labels, sort, direction, since, page, per_page)
    except Exception as e:
        raise e

@mcp.tool()
def update_issue(owner: str, repo: str, issue_number: int, title: Optional[str] = None, body: Optional[str] = None, state: Optional[str] = None, labels: Optional[str] = None, assignees: Optional[str] = None, milestone: Optional[str] = None) -> dict:
    """Update an existing issue in a GitHub repository."""
    try:
        if not owner or not repo or issue_number is None:
            raise ValueError("Owner, repository, and issue number are required")
        return server.update_issue(owner, repo, issue_number, title, body, state, labels, assignees, milestone)
    except Exception as e:
        raise e

@mcp.tool()
def add_issue_comment(owner: str, repo: str, issue_number: int, body: str) -> dict:
    """Add a comment to an existing issue."""
    try:
        if not owner or not repo or issue_number is None or not body:
            raise ValueError("Owner, repository, issue number, and body are required")
        return server.add_issue_comment(owner, repo, issue_number, body)
    except Exception as e:
        raise e

@mcp.tool()
def close_issue(owner: str, repo: str, issue_number: int) -> dict:
    """Close an existing issue in a GitHub repository."""
    try:
        if not owner or not repo or issue_number is None:
            raise ValueError("Owner, repository, and issue number are required")
        return server.close_issue(owner, repo, issue_number)
    except Exception as e:
        raise e

@mcp.tool()
def search_code(q: str, sort: Optional[str] = None, order: Optional[str] = None, per_page: Optional[str] = None, page: Optional[int] = None) -> dict:
    """Search for code in GitHub repositories."""
    try:
        if not q or not isinstance(q, str):
            raise ValueError("Query must be a non-empty string")
        return server.search_code(q, sort, order, per_page, page)
    except Exception as e:
        raise e

@mcp.tool()
def search_issues(q: str, sort: Optional[str] = None, order: Optional[str] = None, per_page: Optional[str] = None, page: Optional[int] = None) -> dict:
    """Search for issues and pull requests in GitHub repositories."""
    try:
        if not q or not isinstance(q, str):
            raise ValueError("Query must be a non-empty string")
        return server.search_issues(q, sort, order, per_page, page)
    except Exception as e:
        raise e

@mcp.tool()
def search_users(q: str, sort: Optional[str] = None, order: Optional[str] = None, per_page: Optional[str] = None, page: Optional[int] = None) -> dict:
    """Search for users on GitHub."""
    try:
        if not q or not isinstance(q, str):
            raise ValueError("Query must be a non-empty string")
        return server.search_users(q, sort, order, per_page, page)
    except Exception as e:
        raise e

@mcp.tool()
def get_issue(owner: str, repo: str, issue_number: int) -> dict:
    """Get detailed information for a specific issue."""
    try:
        if not owner or not repo or issue_number is None:
            raise ValueError("Owner, repository, and issue number are required")
        return server.get_issue(owner, repo, issue_number)
    except Exception as e:
        raise e

@mcp.tool()
def get_pull_request(owner: str, repo: str, pull_number: int) -> dict:
    """Get detailed information for a specific pull request."""
    try:
        if not owner or not repo or pull_number is None:
            raise ValueError("Owner, repository, and pull request number are required")
        return server.get_pull_request(owner, repo, pull_number)
    except Exception as e:
        raise e

@mcp.tool()
def list_pull_requests(owner: str, repo: str, state: Optional[str] = None, head: Optional[str] = None, base: Optional[str] = None, sort: Optional[str] = None, direction: Optional[str] = None, per_page: Optional[str] = None, page: Optional[int] = None) -> dict:
    """List and filter pull requests in a repository."""
    try:
        if not owner or not repo:
            raise ValueError("Owner and repository name are required")
        return server.list_pull_requests(owner, repo, state, head, base, sort, direction, per_page, page)
    except Exception as e:
        raise e

@mcp.tool()
def create_pull_request_review(owner: str, repo: str, pull_number: int, body: str, event: str, commit_id: Optional[str] = None, comments: Optional[str] = None) -> dict:
    """Create a review for a pull request."""
    try:
        if not owner or not repo or pull_number is None or not body or not event:
            raise ValueError("Owner, repository, pull request number, body, and event are required")
        return server.create_pull_request_review(owner, repo, pull_number, body, event, commit_id, comments)
    except Exception as e:
        raise e

@mcp.tool()
def merge_pull_request(owner: str, repo: str, pull_number: int, commit_title: Optional[str] = None, commit_message: Optional[str] = None, merge_method: Optional[str] = None) -> dict:
    """Merge a pull request."""
    try:
        if not owner or not repo or pull_number is None:
            raise ValueError("Owner, repository, and pull request number are required")
        return server.merge_pull_request(owner, repo, pull_number, commit_title, commit_message, merge_method)
    except Exception as e:
        raise e

@mcp.tool()
def get_pull_request_files(owner: str, repo: str, pull_number: int) -> dict:
    """Get list of files changed in a pull request."""
    try:
        if not owner or not repo or pull_number is None:
            raise ValueError("Owner, repository, and pull request number are required")
        return server.get_pull_request_files(owner, repo, pull_number)
    except Exception as e:
        raise e

@mcp.tool()
def get_pull_request_status(owner: str, repo: str, pull_number: int) -> dict:
    """Get comprehensive status of all status checks for a pull request."""
    try:
        if not owner or not repo or pull_number is None:
            raise ValueError("Owner, repository, and pull request number are required")
        return server.get_pull_request_status(owner, repo, pull_number)
    except Exception as e:
        raise e

@mcp.tool()
def update_pull_request_branch(owner: str, repo: str, pull_number: int, expected_head_sha: Optional[str] = None) -> dict:
    """Update pull request branch with latest changes from base branch."""
    try:
        if not owner or not repo or pull_number is None:
            raise ValueError("Owner, repository, and pull request number are required")
        return server.update_pull_request_branch(owner, repo, pull_number, expected_head_sha)
    except Exception as e:
        raise e

@mcp.tool()
def get_pull_request_comments(owner: str, repo: str, pull_number: int) -> dict:
    """Get review comments for a pull request."""
    try:
        if not owner or not repo or pull_number is None:
            raise ValueError("Owner, repository, and pull request number are required")
        return server.get_pull_request_comments(owner, repo, pull_number)
    except Exception as e:
        raise e

@mcp.tool()
def get_pull_request_reviews(owner: str, repo: str, pull_number: int) -> dict:
    """Get reviews for a pull request."""
    try:
        if not owner or not repo or pull_number is None:
            raise ValueError("Owner, repository, and pull request number are required")
        return server.get_pull_request_reviews(owner, repo, pull_number)
    except Exception as e:
        raise e

@mcp.tool()
def list_user_repositories(type: Optional[str] = None, sort: Optional[str] = None, direction: Optional[str] = None, per_page: Optional[str] = None, page: Optional[int] = None) -> dict:
    """List repositories for the current user."""
    try:
        return server.list_user_repositories(type, sort, direction, per_page, page)
    except Exception as e:
        raise e

@mcp.tool()
def get_github_user_info() -> dict:
    """Get GitHub user information for the current authenticated user."""
    try:
        return server.get_github_user_info()
    except Exception as e:
        raise e

# Section 4: Entry Point
if __name__ == "__main__":
    mcp.run()