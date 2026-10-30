"""quotes_run.py and quotes_router.py: call planning, retries, the training-only guard,
and routing by model name."""

from __future__ import annotations

import importlib.util
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import ModuleType
from typing import Any

import httpx
import pandas as pd
import pytest

from micromotives_datasets import quotes as q

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def _load(name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


run = _load("quotes_run")
router = _load("quotes_router")
export = _load("export")


def _rows(people: int, per_person: int, condition: str = "short") -> pd.DataFrame:
    recs = []
    for p in range(people):
        for t in range(per_person):
            recs.append(
                {
                    "study": "s1",
                    "recipe": "r1",
                    "participant_id": f"p{p}",
                    "condition_num": 0,
                    "task_num": t,
                    "persona": json.dumps({"age": 30 + p}),
                    "persona_text": f"Age: {30 + p}",
                    "condition": condition,
                    "outcome": f"question {t}",
                    "response": "3",
                    "scale_min": 1,
                    "scale_max": 5,
                    "factors": "{}",
                }
            )
    return pd.DataFrame(recs)


# --- planning ---------------------------------------------------------------------------


@pytest.mark.parametrize("setting", ["full_persona", "group"])
def test_every_row_is_written_exactly_once(setting: str) -> None:
    rows = _rows(people=13, per_person=9)
    items = run.build_items(rows, setting, 1)
    calls = run.plan_calls(rows, items, setting)
    placed = sorted(i for call in calls for i in call)
    assert placed == list(range(len(rows)))
    assert all(1 <= len(call) <= max(run.MAX_ITEMS, run.GROUP_K) for call in calls)


def test_a_respondent_call_holds_one_person() -> None:
    rows = _rows(people=4, per_person=9)
    calls = run.plan_calls(rows, run.build_items(rows, "full_persona", 1), "full_persona")
    assert all(rows.iloc[c]["participant_id"].nunique() == 1 for c in calls)


def test_group_calls_hold_k_different_people() -> None:
    rows = _rows(people=12, per_person=1)
    calls = run.plan_calls(rows, run.build_items(rows, "group", 1), "group")
    groups = [c for c in calls if len(c) == run.GROUP_K]
    assert len(groups) == 2  # 12 people: two groups of five, two left to their own calls
    assert all(rows.iloc[c]["participant_id"].nunique() == run.GROUP_K for c in groups)


def test_long_conditions_split_calls_to_stay_within_budget() -> None:
    long = "x" * int(run.PROMPT_BUDGET * run.CHARS_PER_TOKEN / 3)
    rows = _rows(people=1, per_person=6, condition=long)
    items = run.build_items(rows, "full_persona", 1)
    calls = run.plan_calls(rows, items, "full_persona")
    assert len(calls) >= 3
    for call in calls:
        assert len(call) == 1 or sum(run.item_tokens(items[i]) for i in call) <= run.PROMPT_BUDGET


def test_refuses_rows_from_a_held_out_study(tmp_path: Path) -> None:
    split = tmp_path / "split.json"
    split.write_text(json.dumps({"seen": ["s1"], "unseen": ["s2"]}))
    run.training_rows_only(pd.DataFrame({"study": ["s1"]}), split)
    with pytest.raises(SystemExit):
        run.training_rows_only(pd.DataFrame({"study": ["s1", "s2"]}), split)


# --- requests ---------------------------------------------------------------------------


def _server(handler: Any, monkeypatch: pytest.MonkeyPatch) -> Any:
    monkeypatch.setattr(run.time, "sleep", lambda _s: None)
    http = httpx.Client(transport=httpx.MockTransport(handler))
    return run.Server("http://pod", "writer", {}, http)


def _models(request: httpx.Request) -> httpx.Response | None:
    if request.url.path == "/v1/models":
        return httpx.Response(200, json={"data": [{"id": "writer", "root": "Qwen/x"}]})
    return None


def test_a_passing_hiccup_is_retried(monkeypatch: pytest.MonkeyPatch) -> None:
    answers = iter(
        [
            httpx.Response(503),
            httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]}),
        ]
    )
    server = _server(lambda r: _models(r) or next(answers), monkeypatch)
    assert server.chat([], {}, 10) == "ok"
    assert not server.failures


def test_a_bad_request_is_not_retried_and_does_not_stop_the_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = []

    def handler(r: httpx.Request) -> httpx.Response:
        if (m := _models(r)) is not None:
            return m
        calls.append(r)
        return httpx.Response(400)

    server = _server(handler, monkeypatch)
    assert server.chat([], {}, 10) == ""
    assert len(calls) == 1 and server.failures == {"http 400": 1}


def test_a_server_that_keeps_failing_gives_up_quietly(monkeypatch: pytest.MonkeyPatch) -> None:
    server = _server(lambda r: _models(r) or httpx.Response(500), monkeypatch)
    assert server.chat([], {}, 10) == ""
    assert server.failures == {"http 500": 1}


def test_refuses_a_pod_not_serving_the_model(monkeypatch: pytest.MonkeyPatch) -> None:
    http = httpx.Client(
        transport=httpx.MockTransport(
            lambda r: httpx.Response(200, json={"data": [{"id": "other"}]})
        )
    )
    with pytest.raises(SystemExit):
        run.Server("http://pod", "writer", {}, http)


# --- the router -------------------------------------------------------------------------


class _Echo(BaseHTTPRequestHandler):
    name = ""

    def log_message(self, *a: Any) -> None:
        pass

    def _send(self, obj: object) -> None:
        body = json.dumps(obj).encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        self._send({"data": [{"id": self.name}]})

    def do_POST(self) -> None:
        raw = self.rfile.read(int(self.headers["Content-Length"]))
        self._send({"backend": self.name, "body": json.loads(raw)})


def _serve(handler: type[BaseHTTPRequestHandler]) -> str:
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{server.server_address[1]}"


@pytest.fixture(scope="module")
def routed() -> str:
    writer = _serve(type("W", (_Echo,), {"name": "writer"}))
    checker = _serve(type("C", (_Echo,), {"name": "checker"}))
    routes = router.parse_routes([f"writer={writer}", f"checker={checker}"])
    return _serve(router.make_handler(routes, "k" * 20))


def test_router_sends_each_model_to_its_backend_with_the_body_untouched(routed: str) -> None:
    auth = {"Authorization": "Bearer " + "k" * 20}
    body = {"model": "checker", "messages": [], "chat_template_kwargs": {"enable_thinking": False}}
    got = httpx.post(f"{routed}/v1/chat/completions", json=body, headers=auth).json()
    assert got == {"backend": "checker", "body": body}
    got = httpx.post(f"{routed}/v1/chat/completions", json=body | {"model": "writer"}, headers=auth)
    assert got.json()["backend"] == "writer"
    listed = httpx.get(f"{routed}/v1/models", headers=auth).json()["data"]
    assert sorted(m["id"] for m in listed) == ["checker", "writer"]


def test_router_refuses_without_the_key_and_unknown_models(routed: str) -> None:
    body = {"model": "writer"}
    assert httpx.post(f"{routed}/v1/chat/completions", json=body).status_code == 401
    wrong = {"Authorization": "Bearer nope"}
    assert httpx.post(f"{routed}/v1/chat/completions", json=body, headers=wrong).status_code == 401
    auth = {"Authorization": "Bearer " + "k" * 20}
    assert httpx.post(f"{routed}/v1/x", json={"model": "nobody"}, headers=auth).status_code == 404
    assert httpx.get(f"{routed}/health").status_code == 200


def test_route_parsing() -> None:
    assert router.parse_routes(["writer=http://a:1/"]) == {"writer": "http://a:1"}
    with pytest.raises(ValueError):
        router.parse_routes(["writer"])


# --- export and join guards -------------------------------------------------------------


def test_export_refuses_synthetic_quotes_in_eval_but_not_real_ones() -> None:
    export.no_synthetic_quotes(pd.DataFrame({"quote": ["a real one"], "synthetic_quote": [False]}))
    with pytest.raises(SystemExit):
        export.no_synthetic_quotes(pd.DataFrame({"quote": ["made"], "synthetic_quote": [True]}))


def test_join_never_puts_a_synthetic_quote_over_a_real_one() -> None:
    row = {
        "study": "s",
        "recipe": "r",
        "participant_id": "p",
        "condition_num": 0,
        "task_num": 0,
        "persona": "{}",
        "condition": "c",
        "outcome": "o",
        "response": "1",
    }
    table = pd.DataFrame(
        [
            {
                **{c: row[c] for c in q.ROW_KEY},
                "input_hash": q.input_hash(row),
                "quote": "made up",
                "passed": True,
            }
        ]
    )
    rows = pd.DataFrame([row | {"quote": "what they wrote", "synthetic_quote": False}])
    out, counts = q.join_quotes(rows, table)
    assert out["quote"].tolist() == ["what they wrote"]
    assert out["synthetic_quote"].tolist() == [False]
    assert counts.stale == 0
