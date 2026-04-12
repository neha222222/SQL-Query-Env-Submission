#!/usr/bin/env python3
"""
Baseline inference script for the SQL Query Environment.

Required environment variables:
  - API_BASE_URL: LLM API endpoint
  - MODEL_NAME: Model identifier
  - HF_TOKEN: Hugging Face API token
"""

import os
import sys

from openai import OpenAI

from sql_query_env.server.environment import SQLQueryEnvironment
from sql_query_env.models import SQLAction
from sql_query_env.server.tasks import TASKS


API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
HF_TOKEN = os.getenv("HF_TOKEN")


def get_llm_client() -> OpenAI:
    return OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)


SYSTEM_PROMPT = """You are an expert SQL query writer. You will be given:
1. A database schema describing tables and their columns
2. A natural language question

Your task is to write a correct SQL SELECT query that answers the question.

Rules:
- Only write SELECT queries
- Use standard SQL syntax compatible with SQLite
- Return ONLY the SQL query, no explanations or markdown
- Do not wrap the query in code blocks or backticks

If you made an error on a previous attempt, you will see feedback. Use it to fix your query."""


def build_prompt(question, schema, feedback=None, error=None):
    parts = [f"## Schema\n{schema}", f"\n## Question\n{question}"]
    if error:
        parts.append(f"\n## Previous Error\n{error}")
    if feedback:
        parts.append(f"\n## Feedback\n{feedback}")
    return "\n".join(parts)


def clean_query(raw):
    q = raw.strip()
    if q.startswith("```"):
        lines = q.split("\n")
        q = "\n".join(l for l in lines if not l.startswith("```")).strip()
    return q


def run_task(client, env, task_def):
    """Run a single task and return the score."""
    task_id = task_def["task_id"]
    difficulty = task_def["difficulty"]

    obs = env.reset(difficulty=difficulty)

    # Find the right task in the task list
    while obs.task_id != task_id and not obs.done:
        obs = env.step(SQLAction(query="SELECT 1"))

    if obs.task_id != task_id:
        return 0.01, 0, False

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    max_attempts = obs.attempts_remaining
    rewards = []

    for step_num in range(1, max_attempts + 1):
        prompt = build_prompt(
            obs.question,
            obs.schema_description,
            feedback=obs.feedback if obs.attempts_used > 0 else None,
            error=obs.error_message if obs.error_message else None,
        )

        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages + [{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=500,
            )
            sql_query = clean_query(response.choices[0].message.content)
        except Exception:
            sql_query = "SELECT 1"

        action = SQLAction(query=sql_query)
        obs = env.step(action)

        reward = round(max(0.01, min(0.99, obs.reward if obs.reward else 0.01)), 2)
        rewards.append(reward)

        action_short = sql_query.replace("\n", " ")[:80]
        print(
            f"[STEP] step={step_num} action={action_short} "
            f"reward={reward:.2f} done={str(obs.task_id != task_id or obs.done).lower()} "
            f"error={obs.error_message or 'null'}",
            flush=True,
        )

        # Task was graded and we moved on or episode ended
        if obs.task_id != task_id or obs.done:
            break

        # If the task was solved (feedback says correct)
        if "Correct!" in obs.feedback:
            break

    final_score = max(rewards) if rewards else 0.01
    final_score = round(max(0.01, min(0.99, final_score)), 2)
    return final_score, len(rewards), final_score > 0.5


def run_inference():
    client = get_llm_client()

    # Run 3 tasks: easy, medium, hard
    task_defs = [
        TASKS[0],  # easy_1
        TASKS[3],  # medium_1
        TASKS[6],  # hard_1
    ]

    all_scores = []

    for task_def in task_defs:
        task_id = task_def["task_id"]
        env = SQLQueryEnvironment()

        print(
            f"[START] task={task_id} env=sql_query_env model={MODEL_NAME}",
            flush=True,
        )

        score, steps, success = run_task(client, env, task_def)
        all_scores.append(score)

        print(
            f"[END] success={str(success).lower()} steps={steps} "
            f"score={score:.3f} rewards={score:.2f}",
            flush=True,
        )

        env.close()


if __name__ == "__main__":
    run_inference()
