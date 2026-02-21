"""Sandboxed code execution tool."""
import subprocess
import tempfile
import os
from pathlib import Path
from langchain_core.tools import tool

try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False


@tool
def run_code(code: str, language: str = "python", timeout: int = 30) -> str:
    """Execute code in a sandboxed environment.
    
    Args:
        code: The code to execute
        language: Programming language (python, javascript, bash)
        timeout: Maximum execution time in seconds
        
    Returns:
        Execution output or error
    """
    # Try Docker first for better isolation
    if DOCKER_AVAILABLE:
        try:
            return _run_in_docker(code, language, timeout)
        except Exception as e:
            # Fall back to local execution
            pass
    
    # Local execution (less safe, but works without Docker)
    return _run_locally(code, language, timeout)


def _run_in_docker(code: str, language: str, timeout: int) -> str:
    """Execute code in a Docker container."""
    client = docker.from_env()
    
    images = {
        "python": "python:3.11-slim",
        "javascript": "node:20-slim",
        "bash": "bash:5",
    }
    
    commands = {
        "python": ["python", "-c", code],
        "javascript": ["node", "-e", code],
        "bash": ["bash", "-c", code],
    }
    
    image = images.get(language, "python:3.11-slim")
    command = commands.get(language, ["python", "-c", code])
    
    try:
        result = client.containers.run(
            image,
            command,
            remove=True,
            timeout=timeout,
            mem_limit="256m",
            network_disabled=True,
        )
        return result.decode("utf-8")
    except docker.errors.ContainerError as e:
        return f"Execution error: {e.stderr.decode('utf-8') if e.stderr else str(e)}"
    except Exception as e:
        raise  # Re-raise to fall back to local execution


def _run_locally(code: str, language: str, timeout: int) -> str:
    """Execute code locally (fallback when Docker unavailable)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        if language == "python":
            file_path = Path(tmpdir) / "script.py"
            cmd = ["python", str(file_path)]
        elif language == "javascript":
            file_path = Path(tmpdir) / "script.js"
            cmd = ["node", str(file_path)]
        elif language == "bash":
            file_path = Path(tmpdir) / "script.sh"
            cmd = ["bash", str(file_path)]
        else:
            return f"Unsupported language: {language}"
        
        file_path.write_text(code)
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=tmpdir,
            )
            
            output = result.stdout
            if result.stderr:
                output += f"\nSTDERR:\n{result.stderr}"
            if result.returncode != 0:
                output += f"\nExit code: {result.returncode}"
            
            return output if output.strip() else "(no output)"
        except subprocess.TimeoutExpired:
            return f"Execution timed out after {timeout} seconds"
        except Exception as e:
            return f"Execution error: {str(e)}"
