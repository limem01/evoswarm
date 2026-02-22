"""File manipulation tools for agents with path traversal protection."""
import os
from pathlib import Path
from langchain_core.tools import tool

WORKSPACE_ROOT = Path(os.getenv("EVOSWARM_WORKSPACE", ".")).resolve()


def _validate_path(file_path: str) -> Path:
    """Validate that a path is within the workspace root.

    Raises:
        ValueError: If the path escapes the workspace root.
    """
    resolved = Path(file_path).resolve()
    if not str(resolved).startswith(str(WORKSPACE_ROOT)):
        raise ValueError(
            f"Access denied: path '{file_path}' is outside workspace root '{WORKSPACE_ROOT}'"
        )
    return resolved


@tool
def read_file(file_path: str) -> str:
    """Read the contents of a file.

    Args:
        file_path: Path to the file to read

    Returns:
        The file contents as a string
    """
    try:
        path = _validate_path(file_path)
        if not path.exists():
            return f"Error: File not found: {file_path}"
        if not path.is_file():
            return f"Error: Not a file: {file_path}"

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        if len(content) > 50000:
            content = content[:50000] + "\n... [truncated]"

        return content
    except ValueError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error reading file: {str(e)}"


@tool
def write_file(file_path: str, content: str) -> str:
    """Write content to a file. Creates parent directories if needed.

    Args:
        file_path: Path to the file to write
        content: Content to write to the file

    Returns:
        Success or error message
    """
    try:
        path = _validate_path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        return f"Successfully wrote {len(content)} bytes to {file_path}"
    except ValueError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error writing file: {str(e)}"


@tool
def list_directory(directory_path: str = ".") -> str:
    """List contents of a directory.

    Args:
        directory_path: Path to the directory to list

    Returns:
        List of files and directories
    """
    try:
        path = _validate_path(directory_path)
        if not path.exists():
            return f"Error: Directory not found: {directory_path}"
        if not path.is_dir():
            return f"Error: Not a directory: {directory_path}"

        items = []
        for item in sorted(path.iterdir()):
            prefix = "[DIR]" if item.is_dir() else "[FILE]"
            items.append(f"{prefix} {item.name}")

        if not items:
            return "Directory is empty"

        return "\n".join(items)
    except ValueError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error listing directory: {str(e)}"
