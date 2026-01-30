"""
Railway entrypoint for FastAPI service.
"""

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
	sys.path.insert(0, str(BACKEND_ROOT))

from src.api.api_service import app

__all__ = ["app"]
