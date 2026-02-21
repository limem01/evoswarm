"""EvoSwarm FastAPI application with WebSocket support."""
import asyncio
import os
import uuid
from contextlib import asynccontextmanager
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.event_bus import event_bus, EventType
from backend.swarm_config import create_evoswarm
from backend.memory.neo4j_memory import Neo4jMemory
from backend.evolution.evaluator import run_evolution_round

load_dotenv()


class ConnectionManager:
    """Manages WebSocket connections for broadcasting events."""
    
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass


manager = ConnectionManager()
memory: Neo4jMemory | None = None
swarm = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global memory, swarm
    
    # Initialize Neo4j memory
    memory = Neo4jMemory(
        uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        user=os.getenv("NEO4J_USER", "neo4j"),
        password=os.getenv("NEO4J_PASSWORD", "password123"),
    )
    await memory.setup_indexes()
    
    # Initialize swarm
    swarm = create_evoswarm()
    
    # Set up event bus broadcasting
    event_bus.set_broadcast_fn(manager.broadcast)
    
    yield
    
    # Cleanup
    if memory:
        memory.close()


app = FastAPI(
    title="EvoSwarm API",
    description="Self-Evolving Multi-Agent Collective",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TaskRequest(BaseModel):
    task: str
    thread_id: str | None = None


class TaskResponse(BaseModel):
    thread_id: str
    result: str
    status: str


class EvolveRequest(BaseModel):
    generations: int = 1


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "evoswarm"}


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
        
        # Extract final message
        final_message = result["messages"][-1].content if result["messages"] else "No response"
        
        # Log task to memory
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


@app.post("/api/evolve")
async def evolve(request: EvolveRequest):
    """Trigger evolution rounds."""
    global memory
    
    if not memory:
        raise HTTPException(status_code=503, detail="Memory not initialized")
    
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


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time event streaming."""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive, handle incoming messages if needed
            data = await websocket.receive_text()
            # Echo back for ping/pong
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
