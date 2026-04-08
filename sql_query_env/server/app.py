"""FastAPI server for the SQL Query Environment."""

from openenv.core.env_server import create_fastapi_app
from sql_query_env.server.environment import SQLQueryEnvironment
from sql_query_env.models import SQLAction, SQLObservation

app = create_fastapi_app(SQLQueryEnvironment, SQLAction, SQLObservation)
