#!/usr/bin/env bash
# Serve the quote writer and checker on a RunPod pod, behind one router (docs/RUNPOD_QUOTES.md).
# Run on the pod after cloning:
#
#   bash scripts/pod_serve_quotes.sh
#
# Starts, in a tmux session "serve": the writer (vLLM, :8000, served as "writer"), then
# the checker (:8001, "checker"), then the router (:4000), which RunPod exposes at
# https://<pod id>-4000.proxy.runpod.net. The quote scripts run on the laptop and call
# that address with QUOTES_API_KEY. Stop the pod in the console when the batches are done.
set -euo pipefail

repo="$(cd "$(dirname "$0")/.." && pwd)"
cd "$repo"
export PATH="$HOME/.local/bin:$PATH"

VLLM="vllm==0.32.0"
WRITER="Qwen/Qwen3.8-27B-FP8"
CHECKER="google/gemma-4-31B-it"
LOGS=/workspace/serve

wait_for() {  # port, pid, name
  for _ in $(seq 1 180); do
    curl -sf "localhost:$1/v1/models" >/dev/null && { echo "$3 up on :$1"; return 0; }
    kill -0 "$2" 2>/dev/null || { echo "$3 exited before it was ready: see $LOGS/$3.log"; return 1; }
    sleep 10
  done
  echo "$3 not ready after 30 minutes: see $LOGS/$3.log"; return 1
}

# --- inside tmux: start the servers one after the other ---------------------------
if [[ "${1:-}" == "--serve" ]]; then
  mkdir -p "$LOGS"
  vllm serve "$WRITER" --served-model-name writer --port 8000 \
    --gpu-memory-utilization 0.45 --max-model-len 16384 >"$LOGS/writer.log" 2>&1 &
  wait_for 8000 $! writer
  # No FP8 copy of Gemma 4 is published; vLLM quantises it to FP8 on load.
  vllm serve "$CHECKER" --served-model-name checker --port 8001 --quantization fp8 \
    --gpu-memory-utilization 0.45 --max-model-len 16384 >"$LOGS/checker.log" 2>&1 &
  wait_for 8001 $! checker
  echo "router on :4000  ->  https://${RUNPOD_POD_ID:-<pod id>}-4000.proxy.runpod.net"
  exec uv run python scripts/quotes_router.py \
    --route writer=http://127.0.0.1:8000 --route checker=http://127.0.0.1:8001 --port 4000
fi

# --- on the pod: check, install, start ----------------------------------------------
[[ -n "${HF_TOKEN:-}" ]] || { echo "HF_TOKEN is not set: check the template"; exit 1; }
[[ ${#QUOTES_API_KEY} -ge 16 ]] || { echo "QUOTES_API_KEY is not set (16+ characters): check the template"; exit 1; }

git config --global credential.helper \
  '!f(){ echo username=x-access-token; echo password=$GITHUB_TOKEN; }; f'
git pull --ff-only

command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync
command -v vllm >/dev/null || uv tool install "$VLLM"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
command -v tmux >/dev/null || { apt-get update -qq && apt-get install -y -qq tmux; }

mkdir -p "$LOGS"
tmux new-session -d -s serve "bash scripts/pod_serve_quotes.sh --serve 2>&1 | tee -a '$LOGS/serve.log'; exec bash"
echo "starting writer, then checker, then router (about 20-30 minutes the first time)"
echo "watch:   tmux attach -t serve    (leave it running: Ctrl-b then d)"
echo "ready when https://${RUNPOD_POD_ID:-<pod id>}-4000.proxy.runpod.net/health shows both true"
