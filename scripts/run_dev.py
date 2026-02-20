"""
Start API, ingestion worker, and Next.js dev server with one command.

Usage (from project root):
  python scripts/run_dev.py

Or with venv explicitly:
  .venv/Scripts/python scripts/run_dev.py    # Windows
  .venv/bin/python scripts/run_dev.py       # macOS/Linux

Starts all three; Ctrl+C stops them all.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    os.chdir(PROJECT_ROOT)

    # Prefer venv Python
    venv_py = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
    if not venv_py.exists():
        venv_py = PROJECT_ROOT / ".venv" / "bin" / "python"
    python = str(venv_py) if venv_py.exists() else sys.executable

    api_cmd = [
        python, "-m", "uvicorn", "src.api.main:app",
        "--reload", "--host", "127.0.0.1", "--port", "8000",
    ]
    worker_cmd = [python, "-m", "src.workers.ingestion_worker"]
    web_cmd = ["npm", "run", "dev"]
    web_cwd = PROJECT_ROOT / "web"

    procs = []
    try:
        procs.append(subprocess.Popen(api_cmd, cwd=PROJECT_ROOT, env=os.environ.copy()))
        procs.append(subprocess.Popen(worker_cmd, cwd=PROJECT_ROOT, env=os.environ.copy()))
        procs.append(subprocess.Popen(web_cmd, cwd=web_cwd, env=os.environ.copy(), shell=(os.name == "nt")))
    except Exception as e:
        print(f"Failed to start: {e}", file=sys.stderr)
        for p in procs:
            p.terminate()
        sys.exit(1)

    print("API: http://127.0.0.1:8000  |  Web: http://localhost:3000  |  Worker: running")
    print("Ctrl+C to stop all.")

    def shutdown(*_):
        for p in procs:
            p.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    for p in procs:
        p.wait()


if __name__ == "__main__":
    main()
