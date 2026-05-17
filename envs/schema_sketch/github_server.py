# Server: GitHub

def create_file(owner: str, repo: str, path: str, content: str, message: str, branch: str) -> dict:
    """
    Create a new file in a GitHub repository.

    Args:
        owner (str): Repository owner (username or organization)
        repo (str): Repository name
        path (str): File path
        content (str): Content to be written to the file
        message (str): Commit message
        branch (str): Branch name

    Returns:
        dict: {
            "commit_sha": str,
            "file_sha": str,
            "path": str
        }
    """
    pass

def search_repositories(q: str, sort: str = None, order: str = None, per_page: str = None, page: int = None) -> dict:
    """
    Search for GitHub repositories.

    Args:
        q (str): Search query (GitHub repository search syntax)
        sort (str): [Optional] Sort field
        order (str): [Optional] Sort direction (asc or desc)
        per_page (str): [Optional] Results per page (max 100)
        page (int): [Optional] Page number

    Returns:
        dict: {
            "repositories": list of dicts with owner, repo, description, stars
        }
    """
    pass

def create_repository(name: str, description: str = None, private: bool = None, autoInit: str = None) -> dict:
    """
    Create a new GitHub repository in your account.

    Args:
        name (str): Repository name
        description (str): [Optional] Repository description
        private (bool): [Optional] Whether repository is private
        autoInit (str): [Optional] Whether to initialize README.md

    Returns:
        dict: {
            "owner": str,
            "repo": str,
            "url": str,
            "created_at": str (ISO 8601)
        }
    """
    pass

def delete_repository(owner: str, repo: str) -> dict:
    """
    Delete a GitHub repository.

    Args:
        owner (str): Repository owner (username or organization)
        repo (str): Repository name

    Returns:
        dict: {
            "owner": str,
            "repo": str,
            "deleted": bool
        }
    """
    pass

def get_file_contents(owner: str, repo: str, path: str, branch: str = None) -> dict:
    """
    Get file or directory contents from GitHub repository.

    Args:
        owner (str): Repository owner (username or organization)
        repo (str): Repository name
        path (str): File path
        branch (str): [Optional] Branch name

    Returns:
        dict: {
            "path": str,
            "content": str,
            "encoding": str,
            "size": int
        }
    """
    pass

def delete_file(owner: str, repo: str, path: str, message: str, branch: str, sha: str) -> dict:
    """
    Delete a file from GitHub repository.

    Args:
        owner (str): Repository owner (username or organization)
        repo (str): Repository name
        path (str): File path to delete
        message (str): Commit message
        branch (str): Branch name
        sha (str): File SHA (required for deletion)

    Returns:
        dict: {
            "commit_sha": str,
            "path": str,
            "deleted": bool
        }
    """
    pass

def push_files(owner: str, repo: str, branch: str, files: list, message: str) -> dict:
    """
    Push multiple files to GitHub repository in a single commit.

    Args:
        owner (str): Repository owner (username or organization)
        repo (str): Repository name
        branch (str): Branch name
        files (list): List of file operations
        message (str): Commit message

    Returns:
        dict: {
            "commit_sha": str,
            "files_changed": int,
            "branch": str
        }
    """
    pass

def create_issue(owner: str, repo: str, title: str, body: str = None, assignees: str = None, labels: str = None, milestone: str = None) -> dict:
    """
    Create a new issue in GitHub repository.

    Args:
        owner (str): Repository owner (username or organization)
        repo (str): Repository name
        title (str): Issue title
        body (str): [Optional] Issue description
        assignees (str): [Optional] List of assignee usernames
        labels (str): [Optional] List of labels
        milestone (str): [Optional] Milestone number

    Returns:
        dict: {
            "issue_number": int,
            "title": str,
            "state": str,
            "created_at": str (ISO 8601)
        }
    """
    pass

def create_pull_request(owner: str, repo: str, title: str, head: str, base: str, body: str = None, draft: str = None, maintainer_can_modify: str = None) -> dict:
    """
    Create a new pull request in GitHub repository.

    Args:
        owner (str): Repository owner (username or organization)
        repo (str): Repository name
        title (str): PR title
        head (str): Branch containing changes
        base (str): Branch to merge into
        body (str): [Optional] PR description
        draft (str): [Optional] Whether to create as draft PR
        maintainer_can_modify (str): [Optional] Whether maintainer can modify

    Returns:
        dict: {
            "pull_number": int,
            "title": str,
            "state": str,
            "created_at": str (ISO 8601)
        }
    """
    pass

def fork_repository(owner: str, repo: str, organization: str = None) -> dict:
    """
    Fork a GitHub repository to your account or specified organization.

    Args:
        owner (str): Repository owner (username or organization)
        repo (str): Repository name
        organization (str): [Optional] Organization to fork to (defaults to personal account)

    Returns:
        dict: {
            "owner": str,
            "repo": str,
            "forked_from": str,
            "created_at": str (ISO 8601)
        }
    """
    pass

def create_branch(owner: str, repo: str, branch: str, from_branch: str = None) -> dict:
    """
    Create a new branch in GitHub repository.

    Args:
        owner (str): Repository owner (username or organization)
        repo (str): Repository name
        branch (str): New branch name
        from_branch (str): [Optional] Source branch (defaults to repository default)

    Returns:
        dict: {
            "branch": str,
            "sha": str,
            "created_at": str (ISO 8601)
        }
    """
    pass

def list_branches(owner: str, repo: str, per_page: int = None, page: int = None) -> list:
    """
    List branches in GitHub repository.

    Args:
        owner (str): Repository owner (username or organization)
        repo (str): Repository name
        per_page (int): [Optional] Results per page (default 30, max 100)
        page (int): [Optional] Page number (default 1)

    Returns:
        list: Each branch contains {
            "name": str,
            "sha": str,
            "protected": bool
        }
    """
    pass

def list_commits(owner: str, repo: str, page: int = None, per_page: str = None, sha: str = None, path: str = None, author: str = None, since: str = None, until: str = None) -> list:
    """
    Get list of commits for GitHub repository branch.

    Args:
        owner (str): Repository owner (username or organization)
        repo (str): Repository name
        page (int): [Optional] Page number
        per_page (str): [Optional] Records per page
        sha (str): [Optional] Branch name or commit SHA
        path (str): [Optional] File path filter
        author (str): [Optional] Author filter
        since (str): [Optional] Start date (ISO 8601)
        until (str): [Optional] End date (ISO 8601)

    Returns:
        list: Each commit contains {
            "sha": str,
            "message": str,
            "author": str,
            "date": str (ISO 8601)
        }
    """
    pass

def list_issues(owner: str, repo: str, state: str = None, labels: str = None, sort: str = None, direction: str = None, since: str = None, page: int = None, per_page: str = None) -> list:
    """
    List issues in GitHub repository with filtering options.

    Args:
        owner (str): Repository owner (username or organization)
        repo (str): Repository name
        state (str): [Optional] State filter
        labels (str): [Optional] Label filter
        sort (str): [Optional] Sort method
        direction (str): [Optional] Sort direction
        since (str): [Optional] Date filter (ISO 8601)
        page (int): [Optional] Page number
        per_page (str): [Optional] Results per page

    Returns:
        list: Each issue contains {
            "issue_number": int,
            "title": str,
            "state": str,
            "created_at": str (ISO 8601)
        }
    """
    pass

def update_issue(owner: str, repo: str, issue_number: int, title: str = None, body: str = None, state: str = None, labels: str = None, assignees: str = None, milestone: str = None) -> dict:
    """
    Update an existing issue in GitHub repository.

    Args:
        owner (str): Repository owner (username or organization)
        repo (str): Repository name
        issue_number (int): Issue number
        title (str): [Optional] New title
        body (str): [Optional] New description
        state (str): [Optional] New state
        labels (str): [Optional] New labels
        assignees (str): [Optional] New assignees
        milestone (str): [Optional] New milestone number

    Returns:
        dict: {
            "issue_number": int,
            "title": str,
            "state": str,
            "updated_at": str (ISO 8601)
        }
    """
    pass

def add_issue_comment(owner: str, repo: str, issue_number: int, body: str) -> dict:
    """
    Add a comment to an existing issue.

    Args:
        owner (str): Repository owner (username or organization)
        repo (str): Repository name
        issue_number (int): Issue number
        body (str): Comment content

    Returns:
        dict: {
            "comment_id": int,
            "issue_number": int,
            "created_at": str (ISO 8601)
        }
    """
    pass

def close_issue(owner: str, repo: str, issue_number: int) -> dict:
    """
    Close an existing issue in GitHub repository.

    Args:
        owner (str): Repository owner (username or organization)
        repo (str): Repository name
        issue_number (int): Issue number

    Returns:
        dict: {
            "issue_number": int,
            "title": str,
            "state": str,
            "closed_at": str (ISO 8601)
        }
    """
    pass

def search_code(q: str, sort: str = None, order: str = None, per_page: str = None, page: int = None) -> dict:
    """
    Search for code in GitHub repositories.

    Args:
        q (str): Search query (GitHub code search syntax)
        sort (str): [Optional] Sort field
        order (str): [Optional] Sort direction (asc or desc)
        per_page (str): [Optional] Results per page (max 100)
        page (int): [Optional] Page number

    Returns:
        dict: {
            "results": list of dicts with repo, path, content, line_number
        }
    """
    pass

def search_issues(q: str, sort: str = None, order: str = None, per_page: str = None, page: int = None) -> dict:
    """
    Search for issues and pull requests in GitHub repositories.

    Args:
        q (str): Search query (GitHub issue search syntax)
        sort (str): [Optional] Sort field
        order (str): [Optional] Sort direction (asc or desc)
        per_page (str): [Optional] Results per page (max 100)
        page (int): [Optional] Page number

    Returns:
        dict: {
            "issues": list of dicts with owner, repo, issue_number, title, state
        }
    """
    pass

def search_users(q: str, sort: str = None, order: str = None, per_page: str = None, page: int = None) -> dict:
    """
    Search for users on GitHub.

    Args:
        q (str): Search query (GitHub user search syntax)
        sort (str): [Optional] Sort field
        order (str): [Optional] Sort direction (asc or desc)
        per_page (str): [Optional] Results per page (max 100)
        page (int): [Optional] Page number

    Returns:
        dict: {
            "users": list of dicts with username, name, company, location
        }
    """
    pass

def get_issue(owner: str, repo: str, issue_number: int) -> dict:
    """
    Get detailed information for a specific issue.

    Args:
        owner (str): Repository owner (username or organization)
        repo (str): Repository name
        issue_number (int): Issue number

    Returns:
        dict: {
            "issue_number": int,
            "title": str,
            "body": str,
            "state": str,
            "created_at": str (ISO 8601),
            "updated_at": str (ISO 8601)
        }
    """
    pass

def get_pull_request(owner: str, repo: str, pull_number: int) -> dict:
    """
    Get detailed information for a specific pull request.

    Args:
        owner (str): Repository owner (username or organization)
        repo (str): Repository name
        pull_number (int): PR number

    Returns:
        dict: {
            "pull_number": int,
            "title": str,
            "body": str,
            "state": str,
            "created_at": str (ISO 8601),
            "updated_at": str (ISO 8601)
        }
    """
    pass

def list_pull_requests(owner: str, repo: str, state: str = None, head: str = None, base: str = None, sort: str = None, direction: str = None, per_page: str = None, page: int = None) -> list:
    """
    List and filter pull requests in repository.

    Args:
        owner (str): Repository owner (username or organization)
        repo (str): Repository name
        state (str): [Optional] State filter
        head (str): [Optional] Head branch filter
        base (str): [Optional] Base branch filter
        sort (str): [Optional] Sort method
        direction (str): [Optional] Sort direction
        per_page (str): [Optional] Results per page
        page (int): [Optional] Page number

    Returns:
        list: Each PR contains {
            "pull_number": int,
            "title": str,
            "state": str,
            "created_at": str (ISO 8601)
        }
    """
    pass

def create_pull_request_review(owner: str, repo: str, pull_number: int, body: str, event: str, commit_id: str = None, comments: str = None) -> dict:
    """
    Create a review for a pull request.

    Args:
        owner (str): Repository owner (username or organization)
        repo (str): Repository name
        pull_number (int): PR number
        body (str): Review comment
        event (str): Review action
        commit_id (str): [Optional] Commit SHA to review
        comments (str): [Optional] Line-level comments

    Returns:
        dict: {
            "review_id": int,
            "pull_number": int,
            "state": str,
            "submitted_at": str (ISO 8601)
        }
    """
    pass

def merge_pull_request(owner: str, repo: str, pull_number: int, commit_title: str = None, commit_message: str = None, merge_method: str = None) -> dict:
    """
    Merge a pull request.

    Args:
        owner (str): Repository owner (username or organization)
        repo (str): Repository name
        pull_number (int): PR number
        commit_title (str): [Optional] Merge commit title
        commit_message (str): [Optional] Merge commit message
        merge_method (str): [Optional] Merge method

    Returns:
        dict: {
            "pull_number": int,
            "merged": bool,
            "merge_commit_sha": str
        }
    """
    pass

def get_pull_request_files(owner: str, repo: str, pull_number: int) -> list:
    """
    Get list of files changed in pull request.

    Args:
        owner (str): Repository owner (username or organization)
        repo (str): Repository name
        pull_number (int): PR number

    Returns:
        list: Each file contains {
            "filename": str,
            "status": str,
            "additions": int,
            "deletions": int
        }
    """
    pass

def get_pull_request_status(owner: str, repo: str, pull_number: int) -> dict:
    """
    Get comprehensive status of all status checks for pull request.

    Args:
        owner (str): Repository owner (username or organization)
        repo (str): Repository name
        pull_number (int): PR number

    Returns:
        dict: {
            "pull_number": int,
            "state": str,
            "statuses": list of dicts with context, state, description
        }
    """
    pass

def update_pull_request_branch(owner: str, repo: str, pull_number: int, expected_head_sha: str = None) -> dict:
    """
    Update pull request branch with latest changes from base branch.

    Args:
        owner (str): Repository owner (username or organization)
        repo (str): Repository name
        pull_number (int): PR number
        expected_head_sha (str): [Optional] Expected HEAD SHA

    Returns:
        dict: {
            "pull_number": int,
            "updated": bool,
            "message": str
        }
    """
    pass

def get_pull_request_comments(owner: str, repo: str, pull_number: int) -> list:
    """
    Get review comments for pull request.

    Args:
        owner (str): Repository owner (username or organization)
        repo (str): Repository name
        pull_number (int): PR number

    Returns:
        list: Each comment contains {
            "comment_id": int,
            "body": str,
            "user": str,
            "created_at": str (ISO 8601)
        }
    """
    pass

def get_pull_request_reviews(owner: str, repo: str, pull_number: int) -> list:
    """
    Get reviews for pull request.

    Args:
        owner (str): Repository owner (username or organization)
        repo (str): Repository name
        pull_number (int): PR number

    Returns:
        list: Each review contains {
            "review_id": int,
            "user": str,
            "state": str,
            "submitted_at": str (ISO 8601)
        }
    """
    pass

def list_user_repositories(type: str = None, sort: str = None, direction: str = None, per_page: str = None, page: int = None) -> list:
    """
    List repositories for the current user.

    Args:
        type (str): [Optional] Repository type (all, owner, public, private, member)
        sort (str): [Optional] Sort method (created, updated, pushed, full_name)
        direction (str): [Optional] Sort direction (asc, desc)
        per_page (str): [Optional] Results per page (default 30, max 100)
        page (int): [Optional] Page number (default 1)

    Returns:
        list: Each repository contains {
            "owner": str,
            "repo": str,
            "description": str,
            "private": bool
        }
    """
    pass

def get_github_user_info() -> dict:
    """
    Get GitHub user information for the current authenticated user.

    Returns:
        dict: {
            "username": str,
            "name": str,
            "email": str,
            "company": str,
            "location": str
        }
    """
    pass
