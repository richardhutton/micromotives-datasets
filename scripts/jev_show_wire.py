#!/usr/bin/env python3
"""Print the exact JSON sent to and received from Jev, for one real call.

Useful for understanding what the SDK actually puts on the wire, and for
checking that nothing unintended (e.g. raw survey data) is leaving the machine.
Authorization headers are redacted.

The call it makes is a REAL production one — `jev.screen_uk_transfer`, driven
through a hooked transport. It used to build its own payload with its own copy
of that prompt's wording, which made this a report on a call nothing else makes
and left a sixth stale copy of the transfer-screen instructions in the repo.
What is printed below is what the pipeline actually sends.

    uv run python scripts/jev_show_wire.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import httpx2 as httpx  # the SDK's vendored httpx; a stock httpx.Client is rejected

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from micromotives_datasets import jev

REDACT = {"authorization", "x-api-key", "api-key", "cookie"}
captured: dict = {}


def _on_request(request: httpx.Request) -> None:
    captured["method"] = request.method
    captured["url"] = str(request.url)
    captured["headers"] = {
        k: ("<redacted>" if k.lower() in REDACT else v) for k, v in request.headers.items()
    }
    captured["body"] = json.loads(request.content.decode())


def _on_response(response: httpx.Response) -> None:
    response.read()
    try:
        captured["response"] = json.loads(response.text)
    except ValueError:
        captured["response"] = response.text[:2000]


TITLE = "Framing in Noisy Informational Environments"
QUESTIONS = """- Experimental Condition
- Do you oppose or support the Patriot Act?
- How certain are you in your support for or opposition to the Patriot Act?
- Distractor shown 1"""


def main() -> int:
    http = httpx.Client(event_hooks={"request": [_on_request], "response": [_on_response]})
    jev.screen_uk_transfer(jev.client(http_client=http), TITLE, QUESTIONS)

    print("=" * 74)
    print(f"{captured['method']} {captured['url']}")
    print("=" * 74)
    print("\n--- REQUEST HEADERS ---")
    print(json.dumps(captured["headers"], indent=2))
    print("\n--- REQUEST BODY ---")
    print(json.dumps(captured["body"], indent=2))
    print("\n--- RESPONSE BODY ---")
    print(json.dumps(captured["response"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
