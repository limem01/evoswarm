"""File manipulation tools for agents."""
import os
from pathlib import Path
from langchain_core.tools import tool


@tool
def read_file(file_path: str) -> str:
    """Read the contents of a file.
    
    Args:
        file_path: Path to the file to read
        
    Returns:
        The file contents as a string
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return f"Error: File not found: {file_path}"
        if not path.is_file():
            return f"Error: Not a file: {file_path}"
        
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Truncate very large files
        if len(content) > 50000:
            content = content[:50000] + "\n... [truncated]"
        
        return content
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
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        
        return f"Successfully wrote {len(content)} bytes to {file_path}"
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
        path = Path(directory_path)
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
    except Exception as e:
        return f"Error listing directory: {str(e)}"
