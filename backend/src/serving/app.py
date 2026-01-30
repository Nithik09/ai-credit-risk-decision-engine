"""
Railway entrypoint for FastAPI service.
"""

from fastapi import FastAPI
from src.api.api_service import app as api_app

app = FastAPI()
app.mount("/", api_app)

__all__ = ["app"]
