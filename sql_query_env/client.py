"""WebSocket client for the SQL Query Environment."""

from openenv.core.env_client import EnvClient
from openenv.core.client_types import StepResult
from sql_query_env.models import SQLAction, SQLObservation, SQLState


class SQLQueryEnv(EnvClient[SQLAction, SQLObservation, SQLState]):
    """Client for interacting with the SQL Query Environment server."""

    def _step_payload(self, action: SQLAction) -> dict:
        return {"query": action.query}

    def _parse_result(self, payload: dict) -> StepResult:
        obs_data = payload.get("observation", payload)
        return StepResult(
            observation=SQLObservation(
                done=payload.get("done", False),
                reward=payload.get("reward"),
                task_id=obs_data.get("task_id", ""),
                difficulty=obs_data.get("difficulty", ""),
                question=obs_data.get("question", ""),
                schema_description=obs_data.get("schema_description", ""),
                query_result=obs_data.get("query_result"),
                expected_result=obs_data.get("expected_result"),
                error_message=obs_data.get("error_message", ""),
                feedback=obs_data.get("feedback", ""),
                attempts_remaining=obs_data.get("attempts_remaining", 0),
                attempts_used=obs_data.get("attempts_used", 0),
            ),
            reward=payload.get("reward"),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: dict) -> SQLState:
        return SQLState(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
            current_task_index=payload.get("current_task_index", 0),
            total_tasks=payload.get("total_tasks", 0),
            tasks_completed=payload.get("tasks_completed", 0),
            cumulative_reward=payload.get("cumulative_reward", 0.0),
            difficulty=payload.get("difficulty", ""),
        )
