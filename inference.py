#!/usr/bin/env python3
"""
Baseline inference script for the SQL Query Environment.

This script demonstrates an AI agent interacting with the SQL Query
Environment using an LLM to generate SQL queries from natural language
questions.

Required environment variables:
  - API_BASE_URL: LLM API endpoint (e.g., https://api.openai.com/v1)
  - MODEL_NAME: Model identifier (e.g., gpt-4o-mini)
  - HF_TOKEN: Hugging Face API token

Usage:
  python inference.py
"""

import json
import os
import sys

from openai import OpenAI

from sql_query_env.server.environment import SQLQueryEnvironment
from sql_query_env.models import SQLAction


# ─── Configuration ───────────────────────────────────────────────────────────

API_BASE_URL = os.environ.get("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.environ.get("MODEL_NAME", "gpt-4o-mini")
HF_TOKEN = os.environ.get("HF_TOKEN", "")


def get_llm_client() -> OpenAI:
    """Create an OpenAI-compatible client."""
    return OpenAI(
        base_url=API_BASE_URL,
        api_key=HF_TOKEN or os.environ.get("OPENAI_API_KEY", ""),
    )


SYSTEM_PROMPT = """You are an expert SQL query writer. You will be given:
1. A database schema describing tables and their columns
2. A natural language question

Your task is to write a correct SQL SELECT query that answers the question.

Rules:
- Only write SELECT queries (no INSERT, UPDATE, DELETE, DROP, etc.)
- Use standard SQL syntax compatible with SQLite
- Return ONLY the SQL query, no explanations or markdown
- Do not wrap the query in code blocks or backticks
- Write clean, readable SQL

If you made an error on a previous attempt, you will see feedback. Use it to fix your query."""


def build_user_prompt(observation) -> str:
    """Build a user prompt from the observation."""
    parts = [
        f"## Database Schema\n{observation.schema_description}",
        f"\n## Question\n{observation.question}",
        f"\n## Task Info\nDifficulty: {observation.difficulty}",
        f"Attempts remaining: {observation.attempts_remaining}",
    ]

    if observation.error_message:
        parts.append(f"\n## Previous Error\n{observation.error_message}")

    if observation.feedback and observation.attempts_used > 0:
        parts.append(f"\n## Feedback\n{observation.feedback}")

    if observation.query_result and observation.attempts_used > 0:
        parts.append(
            f"\n## Your Previous Result (first rows)\n{json.dumps(observation.query_result[:5], indent=2)}"
        )

    return "\n".join(parts)


def run_inference():
    """Run the baseline inference loop."""
    print("[START]")
    print(json.dumps({"status": "starting", "model": MODEL_NAME}))

    client = get_llm_client()
    env = SQLQueryEnvironment()

    # Reset environment
    obs = env.reset()
    total_reward = 0.0
    total_steps = 0

    print("[STEP]")
    print(json.dumps({
        "step": 0,
        "action": "reset",
        "task_id": obs.task_id,
        "difficulty": obs.difficulty,
        "question": obs.question,
    }))

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    while not obs.done:
        # Build prompt for LLM
        user_prompt = build_user_prompt(obs)
        messages_for_call = messages + [{"role": "user", "content": user_prompt}]

        # Get SQL query from LLM
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages_for_call,
                temperature=0.0,
                max_tokens=500,
            )
            sql_query = response.choices[0].message.content.strip()

            # Clean up query (remove markdown code blocks if present)
            if sql_query.startswith("```"):
                lines = sql_query.split("\n")
                sql_query = "\n".join(
                    line for line in lines
                    if not line.startswith("```")
                ).strip()

        except Exception as e:
            print(f"[STEP] LLM Error: {e}")
            sql_query = "SELECT 1"  # Fallback

        # Step the environment
        action = SQLAction(query=sql_query)
        obs = env.step(action)
        total_steps += 1

        if obs.reward is not None:
            total_reward += obs.reward

        print("[STEP]")
        print(json.dumps({
            "step": total_steps,
            "task_id": obs.task_id,
            "difficulty": obs.difficulty,
            "query": sql_query,
            "reward": obs.reward,
            "done": obs.done,
            "feedback": obs.feedback,
            "error": obs.error_message or None,
        }, default=str))

        # If task changed (new question), reset conversation context
        if "Moving to task" in obs.feedback or "Correct!" in obs.feedback:
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Final summary
    print("[END]")
    print(json.dumps({
        "status": "completed",
        "total_steps": total_steps,
        "final_reward": obs.reward,
        "total_reward": total_reward,
        "feedback": obs.feedback,
    }, default=str))

    env.close()


if __name__ == "__main__":
    run_inference()
