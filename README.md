# 🧬 EvoSwarm

> A Self-Evolving Multi-Agent Collective powered by LangGraph

EvoSwarm is an autonomous AI system where multiple specialized agents collaborate on tasks and continuously improve through evolutionary training. The collective learns from successful task completions, trains LoRA adapters, and merges them to create increasingly capable model variants.

## ✨ Features

- **8 Specialized Agents**: Architect, Coder, Critic, Researcher, Tester, Optimizer, Memory Curator, and Evolutor
- **Dynamic Handoffs**: Agents seamlessly pass tasks based on expertise
- **Evolutionary Learning**: Automatic LoRA training from successful task outputs
- **Model Merging**: Combines best-performing adapters using MergeKit
- **Knowledge Graph**: Neo4j-backed collective memory and lineage tracking
- **Real-time Dashboard**: 3D visualization of evolution tree and live agent activity

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                    │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐      │
│  │ Evolution Tree│ │  Agent Feed   │ │ Metrics Panel │      │
│  │   (3D Graph)  │ │  (WebSocket)  │ │               │      │
│  └───────────────┘ └───────────────┘ └───────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                       │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                    LangGraph Swarm                      │ │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐         │ │
│  │  │Arch. │→│Coder │→│Critic│→│Tester│→│Optim.│         │ │
│  │  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘         │ │
│  │           ┌──────────┐ ┌──────────┐                    │ │
│  │           │Researcher│ │MemCurator│                    │ │
│  │           └──────────┘ └──────────┘                    │ │
│  │                    ┌──────────┐                         │ │
│  │                    │ Evolutor │                         │ │
│  │                    └──────────┘                         │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
         │                                    │
         ▼                                    ▼
┌─────────────────┐                 ┌─────────────────────────┐
│     Neo4j       │                 │    Evolution Engine     │
│  Memory Graph   │                 │  ┌─────────────────────┐│
│                 │                 │  │ Data Generator      ││
│  - Tasks        │                 │  │ LoRA Trainer        ││
│  - Learnings    │                 │  │ Model Merger        ││
│  - Lineage      │                 │  │ Evaluator           ││
└─────────────────┘                 │  └─────────────────────┘│
                                    └─────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose
- Ollama with a model installed (e.g., `llama3.1:8b-instruct-q4_K_M`)

### Option 1: Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/evoswarm.git
cd evoswarm

# Copy environment file
cp .env.example .env

# Start all services
docker-compose up -d

# Access the dashboard at http://localhost:3000
```

### Option 2: Manual Setup

```bash
# Clone and setup
git clone https://github.com/yourusername/evoswarm.git
cd evoswarm

# Setup Python environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Start Neo4j (Docker)
docker run -d --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password123 \
  neo4j:5.15-community

# Start backend
uvicorn backend.main:app --reload

# In another terminal, setup frontend
cd frontend
npm install
npm run dev
```

## 📖 Usage

### Running Tasks

1. Open the dashboard at `http://localhost:3000`
2. Enter a task in the input field (e.g., "Create a Python function to calculate Fibonacci numbers")
3. Click "Run Task" and watch the agents collaborate in real-time

### Triggering Evolution

1. Run several tasks to build up training data
2. Click "Evolve" to trigger an evolution round
3. Watch the 3D lineage graph update with new model versions

### API Endpoints

```bash
# Run a task
curl -X POST http://localhost:8000/api/run_task \
  -H "Content-Type: application/json" \
  -d '{"task": "Write a hello world program in Python"}'

# Trigger evolution
curl -X POST http://localhost:8000/api/evolve \
  -H "Content-Type: application/json" \
  -d '{"generations": 1}'

# Get evolution lineage
curl http://localhost:8000/api/lineage

# Health check
curl http://localhost:8000/api/health
```

## 🔧 Configuration

Edit `.env` to customize:

```env
# Neo4j connection
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password123

# Ollama settings
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b-instruct-q4_K_M

# Evolution settings
EVOLUTION_INTERVAL=5  # Minimum tasks before evolution
LORA_OUTPUT_DIR=./models/lora
LOGS_DIR=./logs
```

## 🧪 Agent Roles

| Agent | Role | Capabilities |
|-------|------|--------------|
| **Architect** | System design, task decomposition | Plans implementations, coordinates agents |
| **Coder** | Implementation | Writes code, uses git, runs sandboxed code |
| **Critic** | Code review | Scores code 1-10, identifies issues |
| **Researcher** | Information gathering | Analyzes requirements, finds solutions |
| **Tester** | Testing | Writes and runs tests, reports failures |
| **Optimizer** | Performance | Identifies bottlenecks, improves efficiency |
| **Memory Curator** | Knowledge management | Maintains the knowledge graph |
| **Evolutor** | Evolution orchestration | Manages training and model merging |

## 📊 Evolution Pipeline

1. **Data Collection**: Gather successful task completions
2. **Dataset Generation**: Create SFT data from task/result pairs
3. **LoRA Training**: Fine-tune using Unsloth + TRL
4. **Selection**: Choose best-performing variants
5. **Merging**: Combine LoRAs using MergeKit
6. **Lineage Update**: Record evolution in Neo4j

## 🛠️ Development

```bash
# Run tests
pytest tests/

# Format code
black backend/
ruff check backend/

# Type checking
mypy backend/
```

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

## 🤝 Contributing

Contributions welcome! Please read our [Contributing Guide](CONTRIBUTING.md) first.

## ⚠️ Disclaimer

EvoSwarm is experimental software. The self-evolution feature requires significant computational resources and should be monitored. Always review generated code before production use.

