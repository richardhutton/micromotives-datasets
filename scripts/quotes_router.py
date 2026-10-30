"""Serve ONE model at a time on the RunPod pod, switch on request, route by model name.

    QUOTES_API_KEY=... uv run python scripts/quotes_router.py --start writer

The design in docs/QUOTES_SPEC.md section 9: the writer and the checker never share
the GPU. Each gets the whole card while its phase runs, and the runner here asks the
router to switch between phases (write all, check all, rewrite, check again).

Models and their vLLM flags come from scripts/quotes_models.json. Endpoints, all on
one port and all but /health needing `Authorization: Bearer $QUOTES_API_KEY`:

    GET  /health          {"model", "status"}; 200 only when a model is ready
    GET  /admin/state     the full state: model, hf id, status, since, error
    POST /admin/switch    {"model": "checker"}: stop the current server, free the GPU,
                          start the named one. Returns at once (202); poll /admin/state.
    GET  /v1/models       the ready model's list, or an empty one
    POST /v1/...          passed on untouched to the ready model; 409 if the body names
                          any other model, or none is ready

Status runs stopped -> switching (old server stopping, GPU freeing) -> loading (new
server starting) -> ready, or failed with the last error line of that model's log.
"""

from __future__ import annotations

import argparse
import contextlib
import hmac
import json
import os
import signal
import socket
import subprocess
import threading
import time
from collections.abc import Callable
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import httpx

MODELS = Path(__file__).resolve().parent / "quotes_models.json"
LOAD_TIMEOUT = 45 * 60  # a first start downloads the model
STOP_TIMEOUT = 120


def vllm_command(config: dict[str, Any], name: str, port: int) -> list[str]:
    spec = config["models"][name]
    return [
        "vllm",
        "serve",
        spec["hf"],
        "--served-model-name",
        name,
        "--port",
        str(port),
        "--gpu-memory-utilization",
        str(config["gpu_memory_utilization"]),
        *spec["args"],
    ]


def gpu_memory_used_mib() -> int | None:
    """Memory in use on the GPU, or None where there is no nvidia-smi (the tests)."""
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=20,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    return sum(int(x) for x in out.split() if x.strip().isdigit())


def port_open(port: int) -> bool:
    with socket.socket() as s:
        s.settimeout(1)
        return s.connect_ex(("127.0.0.1", port)) == 0


class Manager:
    """Owns the one model server. All changes go through `switch`."""

    def __init__(
        self,
        names: dict[str, str],
        command: Callable[[str], list[str]],
        port: int,
        logs: Path,
        load_timeout: float = LOAD_TIMEOUT,
    ) -> None:
        self.names = names  # served name -> hf id
        self.command = command
        self.port = port
        self.logs = logs
        self.load_timeout = load_timeout
        self.lock = threading.Lock()
        self.proc: subprocess.Popen[bytes] | None = None
        self.generation = 0
        self.state: dict[str, Any] = {"model": None, "hf": None, "status": "stopped", "error": None}
        self._stamp()

    def _stamp(self) -> None:
        self.state["since"] = datetime.now(UTC).isoformat(timespec="seconds")

    def _set(self, **changes: Any) -> None:
        self.state.update(changes)
        self._stamp()

    def snapshot(self) -> dict[str, Any]:
        with self.lock:
            return dict(self.state)

    def switch(self, name: str) -> dict[str, Any]:
        """Start switching to `name` in the background and return the state at once."""
        if name not in self.names:
            raise ValueError(f"unknown model {name!r}; have {sorted(self.names)}")
        with self.lock:
            if self.state["model"] == name and self.state["status"] in (
                "switching",
                "loading",
                "ready",
            ):
                return dict(self.state)
            self.generation += 1
            gen = self.generation
            self._set(model=name, hf=self.names[name], status="switching", error=None)
        threading.Thread(target=self._run_switch, args=(name, gen), daemon=True).start()
        return self.snapshot()

    def _run_switch(self, name: str, gen: int) -> None:
        self._stop()
        with self.lock:
            if gen != self.generation:
                return  # a later switch took over
            log = self.logs / f"{name}.log"
            log.parent.mkdir(parents=True, exist_ok=True)
            out = log.open("wb")
            self.proc = subprocess.Popen(
                self.command(name), stdout=out, stderr=subprocess.STDOUT, start_new_session=True
            )
            proc = self.proc
            self._set(status="loading")
        deadline = time.monotonic() + self.load_timeout
        http = httpx.Client(timeout=5)
        while time.monotonic() < deadline:
            if gen != self.generation:
                return
            if proc.poll() is not None:
                with self.lock:
                    if gen == self.generation:
                        self._set(status="failed", error=last_error(log))
                return
            with contextlib.suppress(httpx.HTTPError, ValueError, KeyError):
                served = http.get(f"http://127.0.0.1:{self.port}/v1/models").json()["data"]
                if any(m["id"] == name for m in served):
                    with self.lock:
                        if gen == self.generation:
                            self._set(status="ready")
                    return
            time.sleep(2)
        with self.lock:
            if gen == self.generation:
                self._set(status="failed", error=f"not ready after {self.load_timeout:.0f}s")

    def _stop(self) -> None:
        """Stop the running server and its children, then wait for the port and GPU."""
        with self.lock:
            proc, self.proc = self.proc, None
        if proc is not None and proc.poll() is None:
            with contextlib.suppress(ProcessLookupError):
                os.killpg(proc.pid, signal.SIGTERM)
            try:
                proc.wait(timeout=60)
            except subprocess.TimeoutExpired:
                with contextlib.suppress(ProcessLookupError):
                    os.killpg(proc.pid, signal.SIGKILL)
                proc.wait(timeout=30)
        deadline = time.monotonic() + STOP_TIMEOUT
        while time.monotonic() < deadline:
            used = gpu_memory_used_mib()
            if not port_open(self.port) and (used is None or used < 2048):
                return
            time.sleep(2)

    def shutdown(self) -> None:
        with self.lock:
            self.generation += 1
        self._stop()


def last_error(log: Path) -> str:
    """The line that says why a server died: the last ERROR or exception line."""
    try:
        lines = log.read_text(errors="replace").splitlines()
    except OSError:
        return "no log"
    for line in reversed(lines):
        if "Error" in line or "ERROR" in line or "Exception" in line:
            return line.strip()[-400:]
    return (lines[-1].strip()[-400:] if lines else "empty log") + " (exited)"


def make_handler(manager: Manager, key: str) -> type[BaseHTTPRequestHandler]:
    http = httpx.Client(timeout=900)

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *args: Any) -> None:  # bodies are never logged
            pass

        def _send(self, status: int, body: bytes, kind: str = "application/json") -> None:
            self.send_response(status)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _json(self, status: int, obj: object) -> None:
            self._send(status, json.dumps(obj).encode())

        def _error(self, status: int, message: str) -> None:
            self._json(status, {"error": {"message": message}})

        def _authorised(self) -> bool:
            given = self.headers.get("Authorization", "").removeprefix("Bearer ").strip()
            if not hmac.compare_digest(given.encode(), key.encode()):
                self._error(401, "missing or wrong API key")
                return False
            return True

        def _body(self) -> bytes:
            return self.rfile.read(int(self.headers.get("Content-Length", 0)))

        def do_GET(self) -> None:
            state = manager.snapshot()
            if self.path == "/health":
                ready = state["status"] == "ready"
                self._json(
                    200 if ready else 503, {"model": state["model"], "status": state["status"]}
                )
                return
            if not self._authorised():
                return
            if self.path == "/admin/state":
                self._json(200, state)
                return
            if self.path == "/v1/models":
                data = []
                if state["status"] == "ready":
                    with contextlib.suppress(httpx.HTTPError, ValueError, KeyError):
                        data = http.get(
                            f"http://127.0.0.1:{manager.port}/v1/models", timeout=5
                        ).json()["data"]
                self._json(200, {"object": "list", "data": data})
                return
            self._error(404, f"no route for GET {self.path}")

        def do_POST(self) -> None:
            if not self._authorised():
                return
            raw = self._body()
            try:
                model = json.loads(raw)["model"]
            except (ValueError, KeyError, TypeError):
                self._error(400, "body must be JSON with a `model` field")
                return
            if self.path == "/admin/switch":
                try:
                    self._json(202, manager.switch(model))
                except ValueError as e:
                    self._error(404, str(e))
                return
            state = manager.snapshot()
            if model != state["model"] or state["status"] != "ready":
                self._error(
                    409, f"serving {state['model']} ({state['status']}), not {model}: switch first"
                )
                return
            try:
                r = http.post(
                    f"http://127.0.0.1:{manager.port}{self.path}",
                    content=raw,
                    headers={"Content-Type": "application/json"},
                )
            except httpx.HTTPError as e:
                self._error(502, f"{model} did not answer: {type(e).__name__}")
                return
            self._send(r.status_code, r.content, r.headers.get("Content-Type", "application/json"))

    return Handler


class Server(ThreadingHTTPServer):
    daemon_threads = True

    def handle_error(self, request: Any, client_address: Any) -> None:
        """A client that hangs up mid-request is routine over the internet; say nothing."""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", help="model to load at once (writer or checker)")
    ap.add_argument("--port", type=int, default=4000, help="the router's public port")
    ap.add_argument("--logs", type=Path, default=Path("/workspace/serve"))
    args = ap.parse_args()
    key = os.environ.get("QUOTES_API_KEY", "")
    if len(key) < 16:
        raise SystemExit("QUOTES_API_KEY must be set (16+ characters): the pod's port is public")
    config = json.loads(MODELS.read_text())
    model_port = int(config["model_port"])
    manager = Manager(
        {name: spec["hf"] for name, spec in config["models"].items()},
        lambda name: vllm_command(config, name, model_port),
        model_port,
        args.logs,
    )
    if args.start:
        manager.switch(args.start)
    print(f"router on :{args.port}, models {sorted(manager.names)}, one at a time", flush=True)
    try:
        Server(("0.0.0.0", args.port), make_handler(manager, key)).serve_forever()
    finally:
        manager.shutdown()


if __name__ == "__main__":
    main()
