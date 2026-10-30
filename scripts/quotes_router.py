"""Route OpenAI-style requests to the model they name. Runs on the RunPod pod.

    QUOTES_API_KEY=... uv run python scripts/quotes_router.py \\
        --route writer=http://127.0.0.1:8000 --route checker=http://127.0.0.1:8001

One address for everything the pod serves (docs/RUNPOD_QUOTES.md). A request's
`model` field picks the backend ("writer", "checker"; each vLLM server is started with
that --served-model-name), and the body is passed on untouched, so model-specific
settings such as the writer's `chat_template_kwargs` arrive exactly as sent. Every
request needs `Authorization: Bearer $QUOTES_API_KEY`, except GET /health.
"""

from __future__ import annotations

import argparse
import contextlib
import hmac
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

import httpx


def make_handler(routes: dict[str, str], key: str) -> type[BaseHTTPRequestHandler]:
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

        def _error(self, status: int, message: str) -> None:
            self._send(status, json.dumps({"error": {"message": message}}).encode())

        def _authorised(self) -> bool:
            given = self.headers.get("Authorization", "").removeprefix("Bearer ").strip()
            if not hmac.compare_digest(given.encode(), key.encode()):
                self._error(401, "missing or wrong API key")
                return False
            return True

        def do_GET(self) -> None:
            if self.path == "/health":
                up = {}
                for name, url in routes.items():
                    try:
                        up[name] = http.get(f"{url}/v1/models", timeout=5).status_code == 200
                    except httpx.HTTPError:
                        up[name] = False
                self._send(200 if all(up.values()) else 503, json.dumps(up).encode())
                return
            if not self._authorised():
                return
            if self.path == "/v1/models":
                data = []
                for url in routes.values():
                    with contextlib.suppress(httpx.HTTPError, ValueError, KeyError):
                        data += http.get(f"{url}/v1/models", timeout=5).json()["data"]
                self._send(200, json.dumps({"object": "list", "data": data}).encode())
                return
            self._error(404, f"no route for GET {self.path}")

        def do_POST(self) -> None:
            if not self._authorised():
                return
            raw = self.rfile.read(int(self.headers.get("Content-Length", 0)))
            try:
                model = json.loads(raw)["model"]
            except (ValueError, KeyError, TypeError):
                self._error(400, "body must be JSON with a `model` field")
                return
            if model not in routes:
                self._error(404, f"unknown model {model!r}; serving {sorted(routes)}")
                return
            try:
                r = http.post(
                    f"{routes[model]}{self.path}",
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


def parse_routes(pairs: list[str]) -> dict[str, str]:
    routes = {}
    for pair in pairs:
        name, sep, url = pair.partition("=")
        if not sep or not name or not url:
            raise ValueError(f"route must be name=url, got {pair!r}")
        routes[name] = url.rstrip("/")
    return routes


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--route", action="append", required=True, help="name=url, repeatable")
    ap.add_argument("--port", type=int, default=4000)
    args = ap.parse_args()
    key = os.environ.get("QUOTES_API_KEY", "")
    if len(key) < 16:
        raise SystemExit("QUOTES_API_KEY must be set (16+ characters): the pod's port is public")
    routes = parse_routes(args.route)
    print(f"routing {sorted(routes)} on :{args.port}", flush=True)
    Server(("0.0.0.0", args.port), make_handler(routes, key)).serve_forever()


if __name__ == "__main__":
    main()
