"""Typed models for the SQL Query Environment."""

from typing import List, Optional, Dict, Any
from openenv.core.env_server import Action, Observation, State


class SQLAction(Action):
    """Agent submits a SQL query to answer the given question."""
    query: str  # The SQL query written by the agent


class SQLObservation(Observation):
    """Feedback returned after executing the agent's SQL query."""
    # Inherited: done (bool), reward (Optional[float]), metadata (dict)
    task_id: str = ""
    difficulty: str = ""  # "easy", "medium", "hard"
    question: str = ""  # Natural language question to answer
    schema_description: str = ""  # Description of tables and columns
    query_result: Optional[List[Dict[str, Any]]] = None  # Result rows from agent's query
    expected_result: Optional[List[Dict[str, Any]]] = None  # Correct result (shown on done)
    error_message: str = ""  # SQL error if query failed
    feedback: str = ""  # Human-readable feedback
    attempts_remaining: int = 0  # How many attempts left
    attempts_used: int = 0


class SQLState(State):
    """Internal state of the SQL environment."""
    # Inherited: episode_id (Optional[str]), step_count (int)
    current_task_index: int = 0
    total_tasks: int = 0
    tasks_completed: int = 0
    cumulative_reward: float = 0.0
    difficulty: str = ""
