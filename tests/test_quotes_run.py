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


# --- the pod's switch, as the runner sees it ----------------------------------------


def _pod(states: list[dict[str, Any]], monkeypatch: pytest.MonkeyPatch) -> tuple[Any, list[str]]:
    monkeypatch.setattr(run.time, "sleep", lambda _s: None)
    calls: list[str] = []
    feed = iter(states)
    last: dict[str, Any] = {}

    def handler(r: httpx.Request) -> httpx.Response:
        calls.append(f"{r.method} {r.url.path}")
        if r.url.path == "/admin/state":
            last.update(next(feed, last))
            return httpx.Response(200, json=last)
        return httpx.Response(202, json={})

    return run.Pod("http://pod", httpx.Client(transport=httpx.MockTransport(handler))), calls


def _st(model: str | None, status: str, **extra: Any) -> dict[str, Any]:
    return {"model": model, "hf": f"hf/{model}", "status": status, "error": None, **extra}


def test_pod_switches_and_waits_until_the_model_is_ready(monkeypatch: pytest.MonkeyPatch) -> None:
    pod, calls = _pod(
        [
            _st("writer", "ready"),
            _st("checker", "switching"),
            _st("checker", "loading"),
            _st("checker", "ready"),
        ],
        monkeypatch,
    )
    assert pod.use("checker")["hf"] == "hf/checker"
    assert "POST /admin/switch" in calls


def test_pod_does_not_switch_when_the_model_is_already_ready(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pod, calls = _pod([_st("writer", "ready")], monkeypatch)
    pod.use("writer")
    assert "POST /admin/switch" not in calls


def test_pod_stops_the_run_when_a_model_fails_to_start(monkeypatch: pytest.MonkeyPatch) -> None:
    pod, _ = _pod(
        [_st("writer", "ready"), _st("checker", "loading"), _st("checker", "failed", error="OOM")],
        monkeypatch,
    )
    with pytest.raises(SystemExit, match="OOM"):
        pod.use("checker")


def test_phases_resume_after_the_last_saved_one() -> None:
    names = [s[0] for s in run.STEPS]
    assert run.next_step(None) == 0
    assert names[run.next_step("written")] == "checked 0"
    assert names[run.next_step("checked 0")] == "rewritten 1"
    assert run.next_step("done") == len(run.STEPS)
    assert [s[1] for s in run.STEPS] == ["writer", "checker"] * (run.REPAIR_ROUNDS + 1)
    with pytest.raises(SystemExit):
        run.next_step("halfway")


# --- the router: one model at a time ---------------------------------------------------

FAKE_VLLM = """
import json, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
name, port, mode = sys.argv[1], int(sys.argv[2]), sys.argv[3]
if mode == "fail":
    print("ValueError: To serve at least one request ... KV cache needed", flush=True)
    sys.exit(1)
class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def log_message(self, *a): pass
    def _send(self, obj):
        b = json.dumps(obj).encode(); self.send_response(200)
        self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_GET(self): self._send({"data": [{"id": name}]})
    def do_POST(self):
        raw = self.rfile.read(int(self.headers["Content-Length"]))
        self._send({"backend": name, "body": json.loads(raw)})
ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()
"""


def _free_port() -> int:
    import socket

    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _serve(handler: type[BaseHTTPRequestHandler]) -> str:
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{server.server_address[1]}"


@pytest.fixture
def pod_router(tmp_path: Path) -> Any:
    import sys
    import time

    script = tmp_path / "fake_vllm.py"
    script.write_text(FAKE_VLLM)
    port = _free_port()
    modes = {"writer": "ok", "checker": "ok", "broken": "fail"}
    manager = router.Manager(
        {n: f"hf/{n}" for n in modes},
        lambda n: [sys.executable, str(script), n, str(port), modes[n]],
        port,
        tmp_path / "logs",
        load_timeout=30,
    )
    url = _serve(router.make_handler(manager, "k" * 20))

    def wait(model: str, status: str) -> dict[str, Any]:
        for _ in range(150):
            state = manager.snapshot()
            if state["model"] == model and state["status"] == status:
                return state
            time.sleep(0.2)
        raise AssertionError(f"never reached {model} {status}: {manager.snapshot()}")

    yield manager, url, wait
    manager.shutdown()


AUTH = {"Authorization": "Bearer " + "k" * 20}


def test_router_loads_one_model_and_refuses_the_other(pod_router: Any) -> None:
    _, url, wait = pod_router
    assert httpx.get(f"{url}/health").status_code == 503  # nothing loaded yet
    assert (
        httpx.post(f"{url}/admin/switch", json={"model": "writer"}, headers=AUTH).status_code == 202
    )
    wait("writer", "ready")
    assert httpx.get(f"{url}/health").json() == {"model": "writer", "status": "ready"}
    body = {"model": "writer", "messages": [], "chat_template_kwargs": {"enable_thinking": False}}
    got = httpx.post(f"{url}/v1/chat/completions", json=body, headers=AUTH).json()
    assert got == {"backend": "writer", "body": body}  # passed on untouched
    other = httpx.post(f"{url}/v1/chat/completions", json=body | {"model": "checker"}, headers=AUTH)
    assert other.status_code == 409


def test_switching_stops_the_old_server_before_the_new_one_answers(pod_router: Any) -> None:
    manager, url, wait = pod_router
    manager.switch("writer")
    wait("writer", "ready")
    first = manager.proc
    httpx.post(f"{url}/admin/switch", json={"model": "checker"}, headers=AUTH)
    wait("checker", "ready")
    assert first is not None and first.poll() is not None  # the writer is gone
    listed = httpx.get(f"{url}/v1/models", headers=AUTH).json()["data"]
    assert [m["id"] for m in listed] == ["checker"]
    back = httpx.post(f"{url}/v1/chat/completions", json={"model": "writer"}, headers=AUTH)
    assert back.status_code == 409
    manager.switch("writer")
    wait("writer", "ready")  # and back again


def test_switching_to_the_ready_model_does_not_restart_it(pod_router: Any) -> None:
    manager, _, wait = pod_router
    manager.switch("writer")
    wait("writer", "ready")
    pid = manager.proc.pid
    manager.switch("writer")
    assert manager.snapshot()["status"] == "ready" and manager.proc.pid == pid


def test_a_model_that_crashes_on_start_is_reported_failed_with_its_error(pod_router: Any) -> None:
    manager, url, wait = pod_router
    manager.switch("broken")
    state = wait("broken", "failed")
    assert "KV cache" in state["error"]
    assert httpx.get(f"{url}/admin/state", headers=AUTH).json()["status"] == "failed"


def test_router_needs_the_key_and_known_models(pod_router: Any) -> None:
    _, url, _ = pod_router
    assert httpx.get(f"{url}/admin/state").status_code == 401
    assert httpx.post(f"{url}/admin/switch", json={"model": "writer"}).status_code == 401
    unknown = httpx.post(f"{url}/admin/switch", json={"model": "nobody"}, headers=AUTH)
    assert unknown.status_code == 404


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


def test_without_the_blind_test_a_check_is_one_call_and_cannot_fail_on_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sent: list[dict[str, Any]] = []

    def handler(r: httpx.Request) -> httpx.Response:
        sent.append(json.loads(r.content))
        verdict = dict.fromkeys(q.CHECKS, True) | {"notes": ""}
        return httpx.Response(
            200, json={"choices": [{"message": {"content": json.dumps(verdict)}}]}
        )

    checker = run.Server(
        "http://pod", "checker", {}, httpx.Client(transport=httpx.MockTransport(handler))
    )
    item = run.build_items(_rows(people=1, per_person=1), "full_persona", 1)[0]
    off = run.check_one(
        checker, {"checker": "C", "blind": "B"}, item, "a quote", False, 3.0, blind=False
    )
    assert len(sent) == 1 and off["failed"] == [] and off["blind_agrees"] is None
    on = run.check_one(checker, {"checker": "C", "blind": "B"}, item, "a quote", False, 3.0)
    assert len(sent) == 3 and "blind_test" in on["failed"]  # the stub's reply has no answer


def test_a_resumed_run_keeps_the_prompt_version_it_started_with() -> None:
    assert run.prompt_version_of({"prompt_version": "v2"}) == "v2"
    old = {"prompts": {"writer_v2.md": "h", "checker_v2.md": "h", "blind_v2.md": "h"}}
    assert run.prompt_version_of(old) == "v2"  # saved before the version was recorded
    assert run.prompt_version_of({}) == run.PROMPT_VERSION
