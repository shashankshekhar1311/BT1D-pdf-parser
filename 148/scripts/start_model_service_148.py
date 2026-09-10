import os
import sys

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("PYTHONPATH", str(ROOT))

if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "9000"))
    reload_enabled = os.getenv("RELOAD", "false").lower() == "true"
    uvicorn.run("148.app.api.model_service:app", host=host, port=port, reload=reload_enabled)
