"""Git tools for version control operations."""
from pathlib import Path
from langchain_core.tools import tool

try:
    from git import Repo, InvalidGitRepositoryError
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False


@tool
def git_init(directory: str = ".") -> str:
    """Initialize a new Git repository.
    
    Args:
        directory: Directory to initialize as a Git repo
        
    Returns:
        Success or error message
    """
    if not GIT_AVAILABLE:
        return "Error: GitPython not installed"
    
    try:
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        
        repo = Repo.init(path)
        return f"Initialized Git repository in {path.absolute()}"
    except Exception as e:
        return f"Error initializing repository: {str(e)}"


@tool
def git_commit(message: str, directory: str = ".") -> str:
    """Stage all changes and commit with a message.
    
    Args:
        message: Commit message
        directory: Path to the Git repository
        
    Returns:
        Success or error message
    """
    if not GIT_AVAILABLE:
        return "Error: GitPython not installed"
    
    try:
        path = Path(directory)
        repo = Repo(path)
        
        # Stage all changes
        repo.git.add(A=True)
        
        # Check if there are changes to commit
        if not repo.index.diff("HEAD") and not repo.untracked_files:
            return "No changes to commit"
        
        # Commit
        commit = repo.index.commit(message)
        return f"Committed: {commit.hexsha[:8]} - {message}"
    except InvalidGitRepositoryError:
        return f"Error: {directory} is not a Git repository"
    except Exception as e:
        return f"Error committing: {str(e)}"


@tool
def git_status(directory: str = ".") -> str:
    """Get the status of a Git repository.
    
    Args:
        directory: Path to the Git repository
        
    Returns:
        Repository status
    """
    if not GIT_AVAILABLE:
        return "Error: GitPython not installed"
    
    try:
        path = Path(directory)
        repo = Repo(path)
        
        status_lines = []
        
        # Changed files
        changed = [item.a_path for item in repo.index.diff(None)]
        if changed:
            status_lines.append("Modified files:")
            for f in changed:
                status_lines.append(f"  M {f}")
        
        # Staged files
        staged = [item.a_path for item in repo.index.diff("HEAD")]
        if staged:
            status_lines.append("Staged files:")
            for f in staged:
                status_lines.append(f"  S {f}")
        
        # Untracked files
        untracked = repo.untracked_files
        if untracked:
            status_lines.append("Untracked files:")
            for f in untracked:
                status_lines.append(f"  ? {f}")
        
        if not status_lines:
            return "Working tree clean"
        
        return "\n".join(status_lines)
    except InvalidGitRepositoryError:
        return f"Error: {directory} is not a Git repository"
    except Exception as e:
        return f"Error getting status: {str(e)}"
