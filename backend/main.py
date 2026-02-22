"""EvoSwarm FastAPI application with WebSocket support and approval system."""
import asyncio
import json
import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.event_bus import event_bus, EventType
from backend.swarm_config import create_evoswarm
from backend.memory.neo4j_memory import Neo4jMemory
from backend.approval import ApprovalManager

load_dotenv()


class ConnectionManager:
    """Manages WebSocket connections for broadcasting events."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in list(self.active_connections):
            try:
                await connection.send_text(message)
            except Exception:
                self.disconnect(connection)


manager = ConnectionManager()
memory: Neo4jMemory | None = None
approval_manager: ApprovalManager | None = None
swarm = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global memory, swarm, approval_manager

    # Initialize Neo4j memory
    memory = Neo4jMemory(
        uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        user=os.getenv("NEO4J_USER", "neo4j"),
        password=os.getenv("NEO4J_PASSWORD", "password123"),
    )
    await memory.setup_indexes()

    # Initialize approval manager
    policy_path = os.getenv("APPROVAL_POLICY_PATH", "./backend/approval/default_policy.json")
    approval_manager = ApprovalManager(
        policy_path=policy_path,
        log_dir=os.getenv("LOGS_DIR", "./logs"),
    )
    approval_manager.set_broadcast_fn(manager.broadcast)

    # Initialize swarm with memory and approval
    swarm = create_evoswarm(memory=memory, approval_manager=approval_manager)

    # Set up event bus broadcasting
    event_bus.set_broadcast_fn(manager.broadcast)

    yield

    # Cleanup
    if memory:
        memory.close()


app = FastAPI(
    title="EvoSwarm API",
    description="Self-Evolving Multi-Agent Collective with PC Control",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve screenshots/logs statically
logs_dir = Path(os.getenv("LOGS_DIR", "./logs"))
logs_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static/logs", StaticFiles(directory=str(logs_dir)), name="logs")


# ── Request/Response Models ──────────────────────────────────


class TaskRequest(BaseModel):
    task: str
    thread_id: str | None = None


class TaskResponse(BaseModel):
    thread_id: str
    result: str
    status: str


class EvolveRequest(BaseModel):
    generations: int = 1


class ApprovalResponse(BaseModel):
    request_id: str
    approved: bool


# ── Health ───────────────────────────────────────────────────


@app.get("/api/health")
async def health_check():
    """Health check endpoint with service status."""
    status = {"status": "healthy", "service": "evoswarm"}

    # Ollama health
    try:
        from backend.ollama_health import check_ollama
        status["ollama"] = await check_ollama()
    except Exception:
        status["ollama"] = {"status": "unknown"}

    # Neo4j health
    try:
        if memory:
            async with memory.driver.session() as session:
                await session.run("RETURN 1")
            status["neo4j"] = {"status": "connected"}
        else:
            status["neo4j"] = {"status": "not_initialized"}
    except Exception as e:
        status["neo4j"] = {"status": "error", "error": str(e)}

    return status


# ── Task Endpoints ───────────────────────────────────────────


@app.post("/api/run_task", response_model=TaskResponse)
async def run_task(request: TaskRequest):
    """Run a task through the swarm."""
    global swarm, memory

    if not swarm:
        raise HTTPException(status_code=503, detail="Swarm not initialized")

    thread_id = request.thread_id or str(uuid.uuid4())

    await event_bus.emit(EventType.TASK_ASSIGNED, {
        "thread_id": thread_id,
        "task": request.task,
    })

    try:
        config = {"configurable": {"thread_id": thread_id}}
        result = await asyncio.to_thread(
            lambda: swarm.invoke(
                {"messages": [{"role": "user", "content": request.task}]},
                config=config,
            )
        )

        final_message = result["messages"][-1].content if result["messages"] else "No response"

        if memory:
            await memory.log_task(thread_id, request.task, final_message)

        await event_bus.emit(EventType.TASK_COMPLETE, {
            "thread_id": thread_id,
            "result": final_message[:500],
        })

        return TaskResponse(
            thread_id=thread_id,
            result=final_message,
            status="complete",
        )
    except Exception as e:
        await event_bus.emit(EventType.ERROR, {
            "thread_id": thread_id,
            "error": str(e),
        })
        raise HTTPException(status_code=500, detail=str(e))


# ── Evolution Endpoints ──────────────────────────────────────


@app.post("/api/evolve")
async def evolve(request: EvolveRequest):
    """Trigger evolution rounds."""
    global memory

    if not memory:
        raise HTTPException(status_code=503, detail="Memory not initialized")

    from backend.evolution.evaluator import run_evolution_round

    results = []
    for i in range(request.generations):
        await event_bus.emit(EventType.EVOLUTION_ROUND_START, {"generation": i + 1})

        result = await run_evolution_round(memory, event_bus)
        results.append(result)

        await event_bus.emit(EventType.EVOLUTION_ROUND_END, {
            "generation": i + 1,
            "result": result,
        })

    return {"status": "complete", "generations": request.generations, "results": results}


@app.get("/api/lineage")
async def get_lineage():
    """Get the evolution lineage graph."""
    global memory

    if not memory:
        raise HTTPException(status_code=503, detail="Memory not initialized")

    graph = await memory.get_evolution_graph()
    return {"nodes": graph["nodes"], "links": graph["links"]}


@app.get("/api/tasks")
async def get_recent_tasks(limit: int = 50):
    """Get recent tasks."""
    global memory

    if not memory:
        raise HTTPException(status_code=503, detail="Memory not initialized")

    tasks = await memory.get_recent_tasks(limit)
    return {"tasks": tasks}


# ── Approval Endpoints ───────────────────────────────────────


@app.get("/api/approvals/pending")
async def get_pending_approvals():
    """Get all pending approval requests."""
    global approval_manager
    if not approval_manager:
        return {"pending": []}
    return {"pending": approval_manager.get_pending()}


@app.post("/api/approvals/resolve")
async def resolve_approval(response: ApprovalResponse):
    """Resolve a pending approval request."""
    global approval_manager
    if not approval_manager:
        raise HTTPException(status_code=503, detail="Approval manager not initialized")

    resolved = approval_manager.resolve(response.request_id, response.approved, "rest_api")
    if not resolved:
        raise HTTPException(status_code=404, detail=f"No pending request with id: {response.request_id}")

    await event_bus.emit(EventType.APPROVAL_RESOLVED, {
        "request_id": response.request_id,
        "approved": response.approved,
    })

    return {"status": "resolved", "request_id": response.request_id, "approved": response.approved}


@app.get("/api/approvals/audit")
async def get_audit_log(limit: int = 100):
    """Get audit log of approval decisions."""
    global approval_manager
    if not approval_manager:
        return {"audit": []}
    return {"audit": approval_manager.get_audit_log(limit)}


# ── WebSocket ────────────────────────────────────────────────


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time events and approval responses."""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()

            if data == "ping":
                await websocket.send_text("pong")
                continue

            # Handle approval responses from frontend
            try:
                msg = json.loads(data)
                if msg.get("type") == "approval_response" and approval_manager:
                    request_id = msg.get("id")
                    approved = msg.get("approved", False)
                    if request_id:
                        approval_manager.resolve(request_id, approved, "websocket")
                        await event_bus.emit(EventType.APPROVAL_RESOLVED, {
                            "request_id": request_id,
                            "approved": approved,
                        })
            except (json.JSONDecodeError, KeyError):
                pass

    except WebSocketDisconnect:
        manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
