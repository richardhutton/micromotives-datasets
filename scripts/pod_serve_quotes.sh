#!/usr/bin/env bash
# Serve the quote models on a RunPod pod, ONE AT A TIME, behind one router
# (docs/QUOTES_SPEC.md section 9, docs/RUNPOD_QUOTES.md). Run on the pod after cloning:
#
#   bash scripts/pod_serve_quotes.sh
#
# Starts the router (:4000, exposed at https://<pod id>-4000.proxy.runpod.net) in a tmux
# session "serve". The router loads the writer with the whole GPU, and switches to the
# checker and back when quotes_run.py (on the laptop) asks it to between phases. Models
# and their vLLM flags: scripts/quotes_models.json. Logs: /workspace/serve/<model>.log.
# State: curl -s localhost:4000/health
set -euo pipefail

repo="$(cd "$(dirname "$0")/.." && pwd)"
cd "$repo"
export PATH="$HOME/.local/bin:$PATH"
VLLM="vllm==0.32.0"

[[ -n "${HF_TOKEN:-}" ]] || { echo "HF_TOKEN is not set: check the template"; exit 1; }
[[ ${#QUOTES_API_KEY} -ge 16 ]] || { echo "QUOTES_API_KEY is not set (16+ characters): check the template"; exit 1; }
[[ -n "${GITHUB_DATASETS_TOKEN:-}" ]] || { echo "GITHUB_DATASETS_TOKEN is not set: check the template"; exit 1; }

command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync
command -v vllm >/dev/null || uv tool install "$VLLM"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
command -v tmux >/dev/null || { apt-get update -qq && apt-get install -y -qq tmux; }

mkdir -p /workspace/serve
tmux new-session -d -s serve \
  "uv run python scripts/quotes_router.py --start writer --port 4000 2>&1 | tee -a /workspace/serve/router.log; exec bash"
echo "router started; loading the writer (a few minutes once downloaded)"
echo "state: curl -s localhost:4000/health   (or https://${RUNPOD_POD_ID:-<pod id>}-4000.proxy.runpod.net/health)"
