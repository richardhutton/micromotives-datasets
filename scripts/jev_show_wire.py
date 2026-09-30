#!/usr/bin/env python3
"""Print the exact JSON sent to and received from Jev, for one real call.

Useful for understanding what the SDK actually puts on the wire, and for
checking that nothing unintended (e.g. raw survey data) is leaving the machine.
Authorization headers are redacted.

    uv run python scripts/jev_show_wire.py
"""

from __future__ import annotations

import json
import sys

import httpx2 as httpx  # the SDK's vendored httpx; a stock httpx.Client is rejected

try:
    from typesafe_sdk import Noul, TypeSafeClient
except ImportError:  # pragma: no cover
    sys.exit("uv add typesafe-sdk first")

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


STATE = """Survey experiment: "Framing in Noisy Informational Environments"

The questions asked of respondents:

- Experimental Condition
- Do you oppose or support the Patriot Act?
- How certain are you in your support for or opposition to the Patriot Act?
- Distractor shown 1"""


def main() -> int:
    http = httpx.Client(event_hooks={"request": [_on_request], "response": [_on_response]})
    client = TypeSafeClient(http_client=http)
    client.system_one(
        state=STATE,
        questions={
            "outcome_needs_us_knowledge": Noul(
                instructions=(
                    "Answering the main outcome question requires knowledge of United "
                    "States law, politics or institutions that a respondent in another "
                    "country would not reliably have."
                )
            )
        },
    )

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
