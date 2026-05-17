# Server: Git

def git_status(repo_path: str) -> str:
    """
    Show the working tree status.
    
    Args:
        repo_path (str): Path to the Git repository
        
    Returns:
        str: Current status of the working directory
    """
    pass

def git_log(repo_path: str, max_count: int = 10, start_timestamp: str = None, end_timestamp: str = None) -> list[dict]:
    """
    Show the commit logs with optional filtering.
    
    Args:
        repo_path (str): Path to the Git repository
        max_count (int): [Optional] Maximum number of commits to show, default is 10
        start_timestamp (str): [Optional] Start timestamp for filtering (ISO 8601 or relative)
        end_timestamp (str): [Optional] End timestamp for filtering (ISO 8601 or relative)
        
    Returns:
        list[dict]: List of commits, each containing:
            "hash": str,
            "author": str,
            "date": str,
            "message": str
    """
    pass

def git_branch(repo_path: str, branch_type: str, contains: str = None, not_contains: str = None) -> list[dict]:
    """
    List Git branches.
    
    Args:
        repo_path (str): Path to the Git repository
        branch_type (str): Type of branches to list ('local', 'remote', or 'all')
        contains (str): [Optional] Filter branches containing specific commit SHA
        not_contains (str): [Optional] Filter branches NOT containing specific commit SHA
        
    Returns:
        list[dict]: List of branches, each containing:
            "name": str,
            "is_current": bool,
            "sha": str
    """
    pass

def git_show(repo_path: str, revision: str, context_lines: int = 10) -> str:
    """
    Show the contents of a commit or specific revision.
    
    Args:
        repo_path (str): Path to the Git repository
        revision (str): Revision (commit hash, branch name, tag) to show
        context_lines (int): [Optional] Number of context lines to show, default is 10
   
    Returns:
        str: Contents of the specified commit
    """
    pass

def git_diff_unstaged(repo_path: str, context_lines: int = 3) -> str:
    """
    Show changes in working directory not yet staged.
    
    Args:
        repo_path (str): Path to the Git repository
        context_lines (int): [Optional] Number of context lines to show, default is 3
        
    Returns:
        str: Diff output of unstaged changes
    """
    pass

def git_diff_staged(repo_path: str, context_lines: int = 3) -> str:
    """
    Show changes that are staged for commit.
    
    Args:
        repo_path (str): Path t Git repository
        context_lines (int): [Optional] Number of context lines to show, default is 3
 
    Returns:
        str: Diff output of staged changes
    """
    pass

def git_diff(repo_path: str, target: str = "main", context_lines: int = 3) -> str:
    """
    Show differences between current state and a target branch or commit.
    
    Args:
        repo_path (str): Path to the Git repository
        target (str): [Optional] Target branch or commit to compare with, default is "main"
        context_lines (int): [Optional] Number of context lines to show, default is 3
 
    Returns:
        str: Diff output comparing current state with target
    """
    pass

def git_add(repo_path: str, files: list[str]) -> dict:
    """
    Add file contents to the staging area.
    
    Args:
        repo_path (str): Path to the Git repository
        files (list[str]): List of file paths to stage
        
    Returns:
        dict: {
            "staged_files": list[str]
        }
    """
    pass

def git_commit(repo_path: str, message: str) -> dict:
    """
    Record changes to the repository.
    
    Args:
        repo_path (str): Path to the Git repository
        message (str): Commit message
        
    Returns:
        dict: {
            "commit_hash": str,
            "message": str
        }
    """
    pass

def git_reset(repo_path: str) -> dict:
    """
    Unstage all staged changes.
    
    Args:
        repo_path (str): Path to the Git repository
        
    Returns:
        dict: {
            "status": str
        }
    """
    pass

def git_create_branch(repo_path: str, branch_name: str, base_branch: str = None) -> dict:
    """
    Create a new branch.
    
    Args:
        repo_path (str): Path to the Git repository
        branch_name (str): Name of the new branch
        base_branch (str): [Optional] Base branch to create from
        
    Returns:
        dict: {
            "branch_name": str,
            "base_branch": str
        }
    """
    pass

def git_checkout(repo_path: str, branch_name: str) -> dict:
    """o the
    Switch branches.
    
    Args:
        repo_path (str): Path to the Git repository
        branch_name (str): Name of the branch to checkout
        
    Returns:
        dict: {
            "current_branch": str
        }
    """
    pass

def git_push(repo_path: str, remote: str = "origin", branch: str = None, force: bool = False) -> dict:
    """
    Push commits to a remote repository.
    
    Args:
        repo_path (str): Path to the Git repository
        remote (str): [Optional] Remote repository name, default is "origin"
        branch (str): [Optional] Branch to push, default is current branch
        force (bool): [Optional] Force push, default is False
        
    Returns:
        dict: {
            "status": str,
            "remote": str,
            "branch": str
        }
    """
    pass

def git_pull(repo_path: str, remote: str = "origin", branch: str = None, rebase: bool = False) -> dict:
    """
    Fetch and integrate changes from a remote repository.
    
    Args:
        repo_path (str): Path to the Git repository
        remote (str): [Optional] Remote repository name, default is "origin"
        branch (str): [Optional] Branch to pull, default is current branch
        rebase (bool): [Optional] Use rebase instead of merge, default is False
        
    Returns:
        dict: {
            "status": str,
            "remote": str,
            "branch": str,
            "updated_files": list[str]
        }
    """
    pass



