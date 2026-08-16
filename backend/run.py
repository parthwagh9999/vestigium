"""ASGI entry point for running the application directly.

Usage:
    uvicorn run:app --reload --port 8000
    OR
    python run.py
"""

from app.main import create_app

app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "run:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
