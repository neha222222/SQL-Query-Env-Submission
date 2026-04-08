"""FastAPI server entry point for the SQL Query Environment."""

import uvicorn
from sql_query_env.server.app import app


def main(host: str = "0.0.0.0", port: int = 7860):
    """Run the environment server."""
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
