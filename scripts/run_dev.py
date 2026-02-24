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
os.chdir(PROJECT_ROOT)

# Load .env before starting subprocesses so they inherit DATABASE_URL, OPENAI_API_KEY, etc.
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass


def _kill_tree(pids: list[int]) -> None:
    """Kill a list of processes and their children (Windows-safe)."""
    for pid in pids:
        try:
            if sys.platform == "win32":
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(pid)],
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
            else:
                os.killpg(os.getpgid(pid), signal.SIGTERM)
        except Exception:
            pass


def main() -> None:
    # Prefer venv Python for reproducible environments
    venv_py = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
    if not venv_py.exists():
        venv_py = PROJECT_ROOT / ".venv" / "bin" / "python"
    python = str(venv_py) if venv_py.exists() else sys.executable

    api_cmd = [
        python, "-m", "uvicorn", "src.api.main:app",
        "--reload", "--reload-dir", str(PROJECT_ROOT / "src"),
        "--host", "127.0.0.1", "--port", "8000",
    ]
    worker_cmd = [python, "-m", "src.workers.ingestion_worker"]
    web_cmd = ["npm", "run", "dev"]
    web_cwd = PROJECT_ROOT / "web"

    procs: list[subprocess.Popen] = []
    flags = subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0

    try:
        procs.append(subprocess.Popen(api_cmd, cwd=PROJECT_ROOT, env=os.environ.copy(),
                                      creationflags=flags))
        procs.append(subprocess.Popen(worker_cmd, cwd=PROJECT_ROOT, env=os.environ.copy(),
                                      creationflags=flags))
        procs.append(subprocess.Popen(web_cmd, cwd=web_cwd, env=os.environ.copy(),
                                      shell=(os.name == "nt"), creationflags=flags))
    except Exception as e:
        print(f"Failed to start: {e}", file=sys.stderr)
        _kill_tree([p.pid for p in procs])
        sys.exit(1)

    print("API: http://127.0.0.1:8000  |  Web: http://localhost:3000  |  Worker: running")
    print("Ctrl+C to stop all.")

    def shutdown(*_):
        _kill_tree([p.pid for p in procs])
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    for p in procs:
        p.wait()


if __name__ == "__main__":
    main()
