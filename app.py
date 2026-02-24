#!/usr/bin/env python3
"""
Run both the FastAPI backend and the Next.js frontend with a single command.

Usage (from project root):
    python app.py              # Start both; frees 3000 and 8000 first on Windows
    python app.py --no-kill    # Start both without freeing ports
    python app.py --reload     # Also enable uvicorn --reload-dir src (dev mode)

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

# Load .env so backend/frontend subprocesses inherit DATABASE_URL, DEFAULT_TENANT_ID, etc.
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

WEB_DIR = PROJECT_ROOT / "web"
BACKEND_PORT = 8000
FRONTEND_PORT = 3000


def _free_port_windows(port: int) -> None:
    """Kill ALL processes (and their children) listening on the given port (Windows)."""
    try:
        out = subprocess.check_output(
            ["netstat", "-ano"],
            creationflags=subprocess.CREATE_NO_WINDOW,
            text=True,
        )
    except Exception:
        return
    pids: set[str] = set()
    for line in out.splitlines():
        if (":%d " % port) in line or (":%d\t" % port) in line or line.endswith(":%d" % port):
            parts = line.split()
            if parts and parts[-1].isdigit() and parts[-1] != "0":
                pids.add(parts[-1])
    for pid in pids:
        try:
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", pid],  # /T also kills child processes
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        except Exception:
            pass


def _free_ports(ports: list[int]) -> None:
    if sys.platform == "win32":
        for port in ports:
            _free_port_windows(port)
        time.sleep(2)  # Give OS time to release sockets


def _kill_process(proc: subprocess.Popen | None) -> None:
    if proc is None:
        return
    try:
        if sys.platform == "win32":
            # /T kills the entire process tree (uvicorn reloader + workers)
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        else:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        proc.wait(timeout=5)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


def main() -> int:
    use_reload = "--reload" in sys.argv

    if "--no-kill" not in sys.argv:
        print("Freeing ports %s and %s if in use ..." % (BACKEND_PORT, FRONTEND_PORT))
        _free_ports([BACKEND_PORT, FRONTEND_PORT])

    backend_proc: subprocess.Popen | None = None
    frontend_proc: subprocess.Popen | None = None

    def cleanup():
        _kill_process(backend_proc)
        _kill_process(frontend_proc)
        # Belt-and-suspenders: free ports again after stopping
        if sys.platform == "win32":
            _free_ports([BACKEND_PORT, FRONTEND_PORT])

    atexit.register(cleanup)

    def sig_handler(signum, frame):
        cleanup()
        sys.exit(0)

    if not sys.platform == "win32":
        signal.signal(signal.SIGINT, sig_handler)
        signal.signal(signal.SIGTERM, sig_handler)

    # Build uvicorn command
    uvicorn_cmd = [
        sys.executable, "-m", "uvicorn",
        "src.api.main:app",
        "--host", "0.0.0.0",
        "--port", str(BACKEND_PORT),
    ]
    if use_reload:
        # Only watch src/ so editing app.py or scripts/ doesn't trigger restarts
        uvicorn_cmd += ["--reload", "--reload-dir", str(PROJECT_ROOT / "src")]
    else:
        uvicorn_cmd += ["--workers", "1"]

    # Start backend (FastAPI)
    print("Starting backend (FastAPI) on http://localhost:%s ..." % BACKEND_PORT)
    backend_proc = subprocess.Popen(
        uvicorn_cmd,
        cwd=str(PROJECT_ROOT),
        stdout=sys.stdout,
        stderr=sys.stderr,
        env={**os.environ},
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
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
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
        )

    print("\nBackend:  http://localhost:%s" % BACKEND_PORT)
    print("Frontend: http://localhost:%s" % FRONTEND_PORT)
    if use_reload:
        print("Reload:   watching src/ for changes")
    print("Press Ctrl+C to stop both.\n")

    try:
        while True:
            if backend_proc.poll() is not None:
                print("Backend exited (code %s). Stopping." % backend_proc.returncode, file=sys.stderr)
                break
            if frontend_proc is not None and frontend_proc.poll() is not None:
                print("Frontend exited. Stopping.", file=sys.stderr)
                break
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        cleanup()

    return 0


if __name__ == "__main__":
    sys.exit(main())
