"""ASGI entry point: `uvicorn macrovoice.server:app --host 0.0.0.0 --port 8000`."""
from .api import create_app
from .config import Settings

app = create_app(Settings.from_env())
