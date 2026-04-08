
# SQL Query Environment for OpenEnv

An OpenEnv-compliant reinforcement learning environment that trains AI agents to write correct SQL queries from natural language questions. The agent interacts with a realistic relational database containing employees, products, orders, and customers.

## Why SQL?

Text-to-SQL is one of the most impactful real-world applications of AI. Business analysts, data scientists, and non-technical stakeholders need to query databases daily. An AI agent that can reliably translate natural language to SQL has massive practical value — from self-service analytics dashboards to conversational database interfaces.

This environment provides a structured training ground where agents learn progressively harder SQL patterns, receiving granular feedback on their attempts.

## Features

- **9 graded tasks** across 3 difficulty levels (easy, medium, hard)
- **Realistic database schema** with 4 interconnected tables (employees, products, orders, customers)
- **Granular reward function** (0.0–1.0) with partial credit for close answers
- **Detailed feedback** on errors: row count mismatches, column mismatches, SQL errors
- **Safety**: Only SELECT queries allowed — no destructive operations
- **Attempt tracking**: 5 attempts per task with efficiency bonuses for first-try solutions
- **Full OpenEnv compliance**: step() / reset() / state() API with typed Pydantic models

## Task Difficulty Levels

| Level | Skills Tested | Example |
|-------|--------------|---------|
| **Easy** | SELECT, WHERE, ORDER BY on single table | "List all Engineering employees by salary" |
| **Medium** | JOINs, GROUP BY, HAVING, aggregation | "Total revenue per category from completed orders" |
| **Hard** | Subqueries, complex JOINs, LIMIT | "Top 3 customers by total spending" |

## Database Schema

```
TABLE employees (id, name, department, salary, hire_date, manager_id)
TABLE products  (id, name, category, price, stock_quantity)
TABLE orders    (id, customer_name, product_id, quantity, order_date, status)
TABLE customers (id, name, email, city, signup_date)
```

## Action / Observation Space

### Action (agent input)
```python
class SQLAction(Action):
    query: str  # SQL SELECT query
```

### Observation (environment output)
```python
class SQLObservation(Observation):
    done: bool                    # Episode finished?
    reward: Optional[float]       # 0.0 - 1.0 reward signal
    task_id: str                  # Current task identifier
    difficulty: str               # "easy" / "medium" / "hard"
    question: str                 # Natural language question
    schema_description: str       # Full schema documentation
    query_result: List[Dict]      # Result rows from agent's query
    expected_result: List[Dict]   # Correct result (shown after task ends)
    error_message: str            # SQL error if query failed
    feedback: str                 # Human-readable feedback
    attempts_remaining: int       # Attempts left for current task
    attempts_used: int            # Attempts used so far
```

### State
```python
class SQLState(State):
    episode_id: Optional[str]
    step_count: int
    current_task_index: int
    total_tasks: int
    tasks_completed: int
    cumulative_reward: float
    difficulty: str
```

## Reward Function

| Outcome | Reward |
|---------|--------|
| Exact match on first attempt | 1.0 |
| Exact match on later attempts | 0.7 – 0.9 (decreasing with attempts) |
| Partial match (some correct rows/columns) | 0.1 – 0.9 |
| SQL error or completely wrong | 0.0 |
| Final episode reward | Average across all tasks |

## Live API (Hugging Face Space)

The environment is deployed at: **https://neha222222-sql-query-env.hf.space**

### Available Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/reset` | Start a new episode, returns the first task |
| `POST` | `/step` | Submit a SQL query, get feedback and reward |
| `GET` | `/state` | Get current environment state |
| `GET` | `/health` | Health check (`{"status": "healthy"}`) |
| `GET` | `/schema` | Get JSON schemas for action/observation models |
| `GET` | `/metadata` | Environment metadata |
| `GET` | `/docs` | Interactive Swagger UI |
| `POST` | `/mcp` | MCP JSON-RPC endpoint (for tool-calling agents) |
| `WS` | `/ws` | WebSocket for persistent sessions |

### Testing with curl

**1. Health check**
```bash
curl https://neha222222-sql-query-env.hf.space/health
# {"status": "healthy"}
```

**2. Reset the environment (start a new episode)**
```bash
curl -X POST https://neha222222-sql-query-env.hf.space/reset \
  -H 'Content-Type: application/json' \
  -d '{}'
```

**3. Submit a SQL query**
```bash
curl -X POST https://neha222222-sql-query-env.hf.space/step \
  -H 'Content-Type: application/json' \
  -d '{"action": {"query": "SELECT name, salary FROM employees WHERE department = '\''Engineering'\'' ORDER BY salary DESC"}}'
```

**4. Check current state**
```bash
curl https://neha222222-sql-query-env.hf.space/state
```

**5. Get action/observation schemas**
```bash
curl https://neha222222-sql-query-env.hf.space/schema
```

**6. MCP endpoint (for tool-calling agents)**
```bash
curl -X POST https://neha222222-sql-query-env.hf.space/mcp \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc": "2.0", "method": "initialize", "id": 1}'
```
> Note: The `/mcp` endpoint expects valid JSON-RPC 2.0 requests. Sending an empty body returns `{"error": {"code": -32700, "message": "Parse error"}}` which is the correct JSON-RPC error for malformed input.

### Testing with Python

```python
import requests

BASE = "https://neha222222-sql-query-env.hf.space"

# Reset
resp = requests.post(f"{BASE}/reset", json={})
obs = resp.json()
print(obs["observation"]["question"])
print(obs["observation"]["schema_description"])

# Step - submit a query
resp = requests.post(f"{BASE}/step", json={
    "action": {"query": "SELECT name, salary FROM employees WHERE department = 'Engineering' ORDER BY salary DESC"}
})
result = resp.json()
print(f"Reward: {result['reward']}")
print(f"Feedback: {result['observation']['feedback']}")
print(f"Done: {result['done']}")
```

### Testing with WebSocket (persistent session)

```python
import asyncio
import json
import websockets

async def test_ws():
    async with websockets.connect("wss://neha222222-sql-query-env.hf.space/ws") as ws:
        # Reset
        await ws.send(json.dumps({"type": "reset"}))
        obs = json.loads(await ws.recv())
        print(f"Task: {obs['observation']['question']}")

        # Step
        await ws.send(json.dumps({
            "type": "step",
            "action": {"query": "SELECT name, salary FROM employees WHERE department = 'Engineering' ORDER BY salary DESC"}
        }))
        result = json.loads(await ws.recv())
        print(f"Reward: {result['reward']}")

asyncio.run(test_ws())
```

## Quickstart (Local Development)

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run locally (direct Python)

```python
from sql_query_env.server.environment import SQLQueryEnvironment
from sql_query_env.models import SQLAction

env = SQLQueryEnvironment()
obs = env.reset()

print(obs.question)
# "List all employees in the Engineering department, ordered by salary descending."

action = SQLAction(query="SELECT name, salary FROM employees WHERE department = 'Engineering' ORDER BY salary DESC")
obs = env.step(action)

print(obs.reward)   # 1.0
print(obs.feedback)  # "Correct! Reward: 1.00. Moving to task 2/3..."
```

### Run as a server

```bash
uvicorn sql_query_env.server.app:app --host 0.0.0.0 --port 7860
```

### Run with Docker

```bash
docker build -t sql-query-env .
docker run -p 7860:7860 sql-query-env
```

### Run baseline inference

```bash
export API_BASE_URL=https://api.openai.com/v1
export MODEL_NAME=gpt-4o-mini
export OPENAI_API_KEY=your-key-here

python inference.py
```

## Project Structure

```
.
├── inference.py                    # Baseline inference script
├── openenv.yaml                    # Environment manifest
├── Dockerfile                      # Container configuration
├── requirements.txt                # Python dependencies
├── pyproject.toml                  # Package metadata
├── README.md                       # This file
└── sql_query_env/
    ├── __init__.py                 # Package exports
    ├── models.py                   # Typed Pydantic models (Action, Observation, State)
    ├── client.py                   # WebSocket client
    └── server/
        ├── __init__.py
        ├── app.py                  # FastAPI server setup
        ├── environment.py          # Core environment logic
        └── tasks.py               # Task definitions + database schema
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `API_BASE_URL` | LLM API endpoint | `https://api.openai.com/v1` |
| `MODEL_NAME` | Model identifier | `gpt-4o-mini` |
| `HF_TOKEN` | Hugging Face API token | — |

## Technical Details

- **Database**: SQLite in-memory (created fresh each episode)
- **Runtime**: Well under 20 minutes for full episode
- **Resources**: < 2 vCPU, < 1 GB memory
- **Framework**: OpenEnv Core + FastAPI + Pydantic
- **Concurrency**: Supports concurrent sessions

