"""Vercel entry point: mounts the FastAPI backend under /api."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from fastapi import FastAPI  # noqa: E402
from app.main import app as backend  # noqa: E402

app = FastAPI()
app.mount("/api", backend)
