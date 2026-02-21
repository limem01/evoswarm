# EvoSwarm

**Self-Evolving Multi-Agent Collective** — A swarm of AI agents that collaborate, learn, and evolve together.

## Overview

EvoSwarm is a multi-agent system built with LangGraph where 8 specialized agents work together to complete complex tasks. The system features:

- **8 Specialized Agents**: Architect, Coder, Critic, Researcher, Tester, Optimizer, Memory Curator, Evolutor
- **Dynamic Handoffs**: Agents pass work to each other based on task requirements
- **Graph Memory**: Neo4j-powered knowledge storage and evolution lineage tracking
- **Self-Evolution**: LoRA fine-tuning + genetic merging to improve agent performance over time
- **Real-Time Dashboard**: 3D visualization of evolution tree + live agent activity feed

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         EvoSwarm                             │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │Architect│──│  Coder  │──│  Critic │──│ Tester  │        │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘        │
│       │            │            │            │              │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │Researcher│ │Optimizer│  │MemCurator│ │Evolutor │        │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘        │
├─────────────────────────────────────────────────────────────┤
│  Neo4j Graph Memory │ Ollama LLM │ WebSocket Streaming      │
└─────────────────────────────────────────────────────────────┘
```

## Requirements

- **GPU**: NVIDIA RTX with 16GB+ VRAM (tested on RTX 5060 Ti)
- **RAM**: 32GB+ system RAM
- **Software**: Python 3.12, Node.js 24+, Docker, Ollama

## Quick Start

### 1. Clone and Setup

```bash
cd C:\Users\khali\evoswarm

# Create conda environment
conda create -n evoswarm python=3.12 -y
conda activate evoswarm

# Install PyTorch with CUDA
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
```

### 2. Start Neo4j

```bash
docker run -d --name neo4j-evoswarm \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password123 \
  -e "NEO4J_PLUGINS=[\"apoc\"]" \
  -v evoswarm-neo4j-data:/data \
  neo4j:5.28
```

### 3. Pull Ollama Model

```bash
ollama pull llama3.1:8b-instruct-q4_K_M
```

### 4. Start Backend

```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

### 6. Open Dashboard

Navigate to http://localhost:3000

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/run_task` | POST | Submit a task to the swarm |
| `/api/evolve` | POST | Trigger manual evolution round |
| `/api/lineage` | GET | Get evolution tree for visualization |
| `/api/health` | GET | Health check |
| `/ws/{client_id}` | WS | Real-time event streaming |

## Example Task

```bash
curl -X POST http://localhost:8000/api/run_task \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Create a Python function to calculate Fibonacci numbers with memoization"}'
```

## Agent Roles

| Agent | Role |
|-------|------|
| **Architect** | Designs system architecture, decomposes tasks |
| **Coder** | Writes production-ready code |
| **Critic** | Reviews code quality (correctness, efficiency, security) |
| **Researcher** | Gathers information and context |
| **Tester** | Writes and runs tests |
| **Optimizer** | Improves performance |
| **Memory Curator** | Manages knowledge graph |
| **Evolutor** | Orchestrates LoRA training + merging |

## Evolution Pipeline

1. **Data Generation**: Extract high-quality task completions
2. **LoRA Training**: Fine-tune agents using Unsloth (4-bit QLoRA)
3. **Genetic Merge**: Combine top-performing adapters via MergeKit
4. **Lineage Tracking**: Record evolution graph in Neo4j
5. **Evaluation**: Compare pre/post evolution performance

## Project Structure

```
evoswarm/
├── backend/
│   ├── agents/          # 8 agent definitions
│   ├── evolution/       # LoRA training, merging, evaluation
│   ├── memory/          # Neo4j graph memory
│   ├── tools/           # File, git, sandbox tools
│   ├── main.py          # FastAPI app
│   └── swarm_config.py  # Swarm compilation
├── frontend/
│   ├── app/             # Next.js pages
│   └── components/      # React components
├── models/lora/         # Saved LoRA adapters
├── logs/                # Training logs
└── docker-compose.yml   # Container orchestration
```

## Tech Stack

- **Backend**: FastAPI, LangGraph, LangChain, Ollama
- **Evolution**: Unsloth (QLoRA), MergeKit, TRL
- **Memory**: Neo4j 5.28
- **Frontend**: Next.js 15, React 19, Three.js, react-force-graph-3d
- **Infra**: Docker, CUDA 12.6

## License

MIT
