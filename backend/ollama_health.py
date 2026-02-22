"""Ollama health check and model management."""
import os
from typing import Any

import httpx


OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


async def check_ollama() -> dict[str, Any]:
    """Check Ollama availability and list models."""
    result: dict[str, Any] = {"status": "disconnected", "base_url": OLLAMA_BASE_URL}

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Check if Ollama is running
            resp = await client.get(f"{OLLAMA_BASE_URL}/api/version")
            if resp.status_code == 200:
                result["status"] = "connected"
                result["version"] = resp.json().get("version", "unknown")

            # List available models
            resp = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            if resp.status_code == 200:
                models = resp.json().get("models", [])
                result["models"] = [
                    {
                        "name": m["name"],
                        "size": m.get("size", 0),
                        "modified_at": m.get("modified_at", ""),
                    }
                    for m in models
                ]
                result["model_count"] = len(models)

                # Check if configured model is available
                configured = os.getenv("OLLAMA_MODEL", "llama3.1:8b-instruct-q4_K_M")
                result["configured_model"] = configured
                result["model_available"] = any(
                    m["name"] == configured or m["name"].startswith(configured.split(":")[0])
                    for m in models
                )

                if not result["model_available"]:
                    result["suggestion"] = f"Run: ollama pull {configured}"

    except httpx.ConnectError:
        result["status"] = "disconnected"
        result["suggestion"] = "Start Ollama: https://ollama.com/download"
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    return result


async def pull_model(model_name: str) -> dict[str, Any]:
    """Trigger a model pull on Ollama."""
    try:
        async with httpx.AsyncClient(timeout=600.0) as client:
            resp = await client.post(
                f"{OLLAMA_BASE_URL}/api/pull",
                json={"name": model_name, "stream": False},
            )
            if resp.status_code == 200:
                return {"status": "success", "model": model_name}
            return {"status": "error", "detail": resp.text}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
