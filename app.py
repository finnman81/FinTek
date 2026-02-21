#!/usr/bin/env python3
"""
Run both the FastAPI backend and the Next.js frontend with a single command.

Usage (from project root):
    python app.py

Backend: http://localhost:8000
Frontend: http://localhost:3000

Press Ctrl+C to stop both.
"""

from __future__ import annotations

import atexit
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
WEB_DIR = PROJECT_ROOT / "web"
BACKEND_PORT = 8000
FRONTEND_PORT = 3000


def _kill_process(proc: subprocess.Popen | None) -> None:
    if proc is None:
        return
    try:
        if sys.platform == "win32":
            proc.terminate()
        else:
            proc.send_signal(signal.SIGTERM)
        proc.wait(timeout=5)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


def main() -> int:
    backend_proc: subprocess.Popen | None = None
    frontend_proc: subprocess.Popen | None = None

    def cleanup():
        _kill_process(backend_proc)
        _kill_process(frontend_proc)

    atexit.register(cleanup)

    def sig_handler(signum, frame):
        cleanup()
        sys.exit(0)

    if not sys.platform == "win32":
        signal.signal(signal.SIGINT, sig_handler)
        signal.signal(signal.SIGTERM, sig_handler)

    # Start backend (FastAPI)
    print("Starting backend (FastAPI) on http://localhost:%s ..." % BACKEND_PORT)
    backend_proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "src.api.main:app",
            "--reload",
            "--host",
            "0.0.0.0",
            "--port",
            str(BACKEND_PORT),
        ],
        cwd=str(PROJECT_ROOT),
        stdout=sys.stdout,
        stderr=sys.stderr,
        env={**os.environ},
    )

    # Start frontend (Next.js)
    if not WEB_DIR.is_dir():
        print("Warning: web/ not found. Backend only. Frontend: cd web && npm run dev", file=sys.stderr)
    else:
        print("Starting frontend (Next.js) on http://localhost:%s ..." % FRONTEND_PORT)
        frontend_proc = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=str(WEB_DIR),
            stdout=sys.stdout,
            stderr=sys.stderr,
            shell=sys.platform == "win32",
            env={**os.environ},
        )

    print("\nBackend:  http://localhost:%s" % BACKEND_PORT)
    print("Frontend: http://localhost:%s" % FRONTEND_PORT)
    print("Press Ctrl+C to stop both.\n")

    try:
        while True:
            if backend_proc.poll() is not None:
                print("Backend exited.", file=sys.stderr)
                break
            if frontend_proc is not None and frontend_proc.poll() is not None:
                print("Frontend exited.", file=sys.stderr)
                break
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        cleanup()

    return 0


if __name__ == "__main__":
    sys.exit(main())
