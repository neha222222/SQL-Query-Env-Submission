"""SQL Query Environment - core game logic."""

import sqlite3
import uuid
from typing import Optional

from openenv.core.env_server import Environment

from sql_query_env.models import SQLAction, SQLObservation, SQLState
from sql_query_env.server.tasks import SCHEMA_DDL, SEED_DATA, SCHEMA_DESCRIPTION, TASKS


def _create_db() -> sqlite3.Connection:
    """Create an in-memory SQLite database with the schema and seed data."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA_DDL)
    conn.executescript(SEED_DATA)
    return conn


def _execute_query(conn: sqlite3.Connection, query: str) -> list[dict]:
    """Execute a SELECT query and return results as list of dicts."""
    cursor = conn.execute(query)
    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _normalize_results(results: list[dict]) -> list[dict]:
    """Normalize query results for comparison: lowercase keys, round floats."""
    normalized = []
    for row in results:
        norm_row = {}
        for k, v in row.items():
            key = k.lower().strip()
            if isinstance(v, float):
                v = round(v, 2)
            norm_row[key] = v
        normalized.append(norm_row)
    return normalized


def _results_match(actual: list[dict], expected: list[dict]) -> tuple[bool, float]:
    """
    Compare query results. Returns (exact_match, partial_score).

    Scoring:
    - 1.0: Exact match (same rows, same values)
    - 0.5-0.9: Partial match (correct rows but minor differences)
    - 0.1-0.4: Has some correct data
    - 0.0: Completely wrong or error
    """
    if not actual and not expected:
        return True, 1.0
    if not actual or not expected:
        return False, 0.0

    norm_actual = _normalize_results(actual)
    norm_expected = _normalize_results(expected)

    # Check exact match (order-insensitive for rows)
    def row_to_tuple(row):
        return tuple(sorted(row.items()))

    actual_set = set(row_to_tuple(r) for r in norm_actual)
    expected_set = set(row_to_tuple(r) for r in norm_expected)

    if actual_set == expected_set:
        return True, 1.0

    # Partial scoring based on row overlap
    if len(expected_set) == 0:
        return False, 0.0

    matching_rows = actual_set & expected_set
    row_overlap = len(matching_rows) / len(expected_set)

    # Check if column count matches
    actual_cols = set()
    expected_cols = set()
    for r in norm_actual:
        actual_cols.update(r.keys())
    for r in norm_expected:
        expected_cols.update(r.keys())

    col_match = len(actual_cols & expected_cols) / max(len(expected_cols), 1)

    # Combined partial score
    partial = round(0.6 * row_overlap + 0.4 * col_match, 2)
    partial = min(partial, 0.9)  # Cap at 0.9 for non-exact matches

    return False, partial


class SQLQueryEnvironment(Environment):
    """
    An environment where an AI agent learns to write SQL queries.

    The agent receives a natural language question and a database schema,
    then must write a SQL query that produces the correct result.

    Tasks are graded at three difficulty levels:
    - Easy: Single table queries (SELECT, WHERE, ORDER BY)
    - Medium: JOINs, GROUP BY, HAVING, aggregation
    - Hard: Subqueries, complex JOINs, window functions
    """

    SUPPORTS_CONCURRENT_SESSIONS = True

    def __init__(self):
        self._db: Optional[sqlite3.Connection] = None
        self._state = SQLState()
        self._current_task = None
        self._attempts_used = 0
        self._max_attempts = 5
        self._task_list = []

    def reset(self, seed=None, episode_id=None, **kwargs) -> SQLObservation:
        """Initialize a new episode with all tasks."""
        # Create fresh database
        if self._db:
            self._db.close()
        self._db = _create_db()

        # Determine which tasks to use based on kwargs
        difficulty = kwargs.get("difficulty", None)
        if difficulty and difficulty in ("easy", "medium", "hard"):
            self._task_list = [t for t in TASKS if t["difficulty"] == difficulty]
        else:
            # Default: one task from each difficulty
            self._task_list = [
                TASKS[0],  # easy
                TASKS[3],  # medium
                TASKS[6],  # hard
            ]

        self._current_task = self._task_list[0]
        self._attempts_used = 0
        self._max_attempts = self._current_task["max_attempts"]

        self._state = SQLState(
            episode_id=episode_id or str(uuid.uuid4()),
            step_count=0,
            current_task_index=0,
            total_tasks=len(self._task_list),
            tasks_completed=0,
            cumulative_reward=0.0,
            difficulty=self._current_task["difficulty"],
        )

        return SQLObservation(
            done=False,
            reward=None,
            task_id=self._current_task["task_id"],
            difficulty=self._current_task["difficulty"],
            question=self._current_task["question"],
            schema_description=SCHEMA_DESCRIPTION,
            query_result=None,
            expected_result=None,
            error_message="",
            feedback=f"Task 1/{len(self._task_list)}: Write a SQL query to answer the question. You have {self._max_attempts} attempts.",
            attempts_remaining=self._max_attempts,
            attempts_used=0,
        )

    def step(self, action: SQLAction, timeout_s=None, **kwargs) -> SQLObservation:
        """Execute the agent's SQL query and evaluate it."""
        if self._current_task is None:
            return SQLObservation(
                done=False,
                reward=0.0,
                error_message="No active episode. Call /reset first.",
                feedback="You must reset the environment before stepping.",
            )

        self._state.step_count += 1
        self._attempts_used += 1

        task = self._current_task
        query = action.query.strip()

        # Safety: only allow SELECT queries
        if not query.upper().startswith("SELECT"):
            return SQLObservation(
                done=False,
                reward=0.0,
                task_id=task["task_id"],
                difficulty=task["difficulty"],
                question=task["question"],
                schema_description=SCHEMA_DESCRIPTION,
                query_result=None,
                expected_result=None,
                error_message="Only SELECT queries are allowed.",
                feedback="Your query must start with SELECT. Please try again.",
                attempts_remaining=self._max_attempts - self._attempts_used,
                attempts_used=self._attempts_used,
            )

        # Execute agent's query
        try:
            actual_results = _execute_query(self._db, query)
        except Exception as e:
            error_msg = str(e)
            remaining = self._max_attempts - self._attempts_used
            if remaining <= 0:
                return self._fail_task(task, error_msg)
            return SQLObservation(
                done=False,
                reward=0.0,
                task_id=task["task_id"],
                difficulty=task["difficulty"],
                question=task["question"],
                schema_description=SCHEMA_DESCRIPTION,
                query_result=None,
                expected_result=None,
                error_message=error_msg,
                feedback=f"SQL error: {error_msg}. You have {remaining} attempts remaining.",
                attempts_remaining=remaining,
                attempts_used=self._attempts_used,
            )

        # Execute reference query to get expected results
        expected_results = _execute_query(self._db, task["reference_query"])

        # Compare results
        exact_match, partial_score = _results_match(actual_results, expected_results)

        # Apply difficulty multiplier to reward
        difficulty_multiplier = {"easy": 1.0, "medium": 1.0, "hard": 1.0}
        reward = partial_score * difficulty_multiplier[task["difficulty"]]

        # Determine attempt efficiency bonus
        if exact_match and self._attempts_used == 1:
            reward = 1.0  # Perfect score for first-try correct
        elif exact_match:
            # Small penalty for needing multiple attempts
            reward = max(0.7, 1.0 - 0.1 * (self._attempts_used - 1))

        remaining = self._max_attempts - self._attempts_used

        if exact_match:
            return self._succeed_task(task, actual_results, expected_results, reward)

        if remaining <= 0:
            return self._fail_task(task, "", actual_results, expected_results, partial_score)

        # Provide feedback for incorrect answer
        feedback_parts = [f"Not quite right (similarity: {partial_score:.0%})."]
        if len(actual_results) != len(expected_results):
            feedback_parts.append(
                f"Expected {len(expected_results)} rows, got {len(actual_results)}."
            )
        if actual_results and expected_results:
            actual_cols = set(actual_results[0].keys())
            expected_cols = set(expected_results[0].keys())
            if actual_cols != expected_cols:
                feedback_parts.append(
                    f"Column mismatch. Expected columns: {sorted(expected_cols)}"
                )
        feedback_parts.append(f"You have {remaining} attempts remaining.")

        return SQLObservation(
            done=False,
            reward=reward,
            task_id=task["task_id"],
            difficulty=task["difficulty"],
            question=task["question"],
            schema_description=SCHEMA_DESCRIPTION,
            query_result=actual_results[:10],  # Limit shown rows
            expected_result=None,  # Don't reveal expected until done
            error_message="",
            feedback=" ".join(feedback_parts),
            attempts_remaining=remaining,
            attempts_used=self._attempts_used,
        )

    def _succeed_task(self, task, actual, expected, reward):
        """Handle successful task completion and move to next task."""
        self._state.tasks_completed += 1
        self._state.cumulative_reward += reward

        # Move to next task
        next_index = self._state.current_task_index + 1
        if next_index < len(self._task_list):
            # More tasks to go
            self._state.current_task_index = next_index
            self._current_task = self._task_list[next_index]
            self._attempts_used = 0
            self._max_attempts = self._current_task["max_attempts"]
            self._state.difficulty = self._current_task["difficulty"]

            return SQLObservation(
                done=False,
                reward=reward,
                task_id=self._current_task["task_id"],
                difficulty=self._current_task["difficulty"],
                question=self._current_task["question"],
                schema_description=SCHEMA_DESCRIPTION,
                query_result=actual[:10],
                expected_result=expected[:10],
                error_message="",
                feedback=(
                    f"Correct! Reward: {reward:.2f}. "
                    f"Moving to task {next_index + 1}/{len(self._task_list)} "
                    f"(difficulty: {self._current_task['difficulty']}). "
                    f"You have {self._max_attempts} attempts."
                ),
                attempts_remaining=self._max_attempts,
                attempts_used=0,
            )
        else:
            # All tasks completed
            avg_reward = self._state.cumulative_reward / len(self._task_list)
            return SQLObservation(
                done=True,
                reward=avg_reward,
                task_id=task["task_id"],
                difficulty=task["difficulty"],
                question=task["question"],
                schema_description=SCHEMA_DESCRIPTION,
                query_result=actual[:10],
                expected_result=expected[:10],
                error_message="",
                feedback=(
                    f"All tasks completed! "
                    f"Tasks solved: {self._state.tasks_completed}/{len(self._task_list)}. "
                    f"Average reward: {avg_reward:.2f}."
                ),
                attempts_remaining=0,
                attempts_used=self._attempts_used,
            )

    def _fail_task(self, task, error_msg="", actual=None, expected=None, partial_score=0.0):
        """Handle task failure (out of attempts) and move to next task."""
        self._state.cumulative_reward += partial_score

        # Execute reference to show expected
        if expected is None:
            expected = _execute_query(self._db, task["reference_query"])

        next_index = self._state.current_task_index + 1
        if next_index < len(self._task_list):
            self._state.current_task_index = next_index
            self._current_task = self._task_list[next_index]
            self._attempts_used = 0
            self._max_attempts = self._current_task["max_attempts"]
            self._state.difficulty = self._current_task["difficulty"]

            return SQLObservation(
                done=False,
                reward=partial_score,
                task_id=self._current_task["task_id"],
                difficulty=self._current_task["difficulty"],
                question=self._current_task["question"],
                schema_description=SCHEMA_DESCRIPTION,
                query_result=actual[:10] if actual else None,
                expected_result=expected[:10] if expected else None,
                error_message=error_msg,
                feedback=(
                    f"Out of attempts for task '{task['task_id']}'. "
                    f"Moving to task {next_index + 1}/{len(self._task_list)} "
                    f"(difficulty: {self._current_task['difficulty']}). "
                    f"You have {self._max_attempts} attempts."
                ),
                attempts_remaining=self._max_attempts,
                attempts_used=0,
            )
        else:
            avg_reward = self._state.cumulative_reward / len(self._task_list)
            return SQLObservation(
                done=True,
                reward=avg_reward,
                task_id=task["task_id"],
                difficulty=task["difficulty"],
                question=task["question"],
                schema_description=SCHEMA_DESCRIPTION,
                query_result=actual[:10] if actual else None,
                expected_result=expected[:10] if expected else None,
                error_message=error_msg,
                feedback=(
                    f"All tasks attempted. "
                    f"Tasks solved: {self._state.tasks_completed}/{len(self._task_list)}. "
                    f"Average reward: {avg_reward:.2f}."
                ),
                attempts_remaining=0,
                attempts_used=self._attempts_used,
            )

    @property
    def state(self) -> SQLState:
        return self._state

    def close(self):
        if self._db:
            self._db.close()
            self._db = None
