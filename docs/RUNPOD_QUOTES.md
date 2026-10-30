# Writing quotes with models on RunPod

The models run on a RunPod pod behind one router; everything else runs here. Design:
`docs/QUOTES_SPEC.md`.

- **On the pod:** ONE model at a time with the whole GPU, the writer (Qwen3.8-27B FP8)
  or the checker (Gemma 4 31B, quantised to FP8 on load), served by vLLM behind a router
  (`scripts/quotes_router.py`) on one address that needs an API key. The router switches
  model when asked; models and flags are in `scripts/quotes_models.json`.
- **Here:** `scripts/quotes_run.py` sends the rows in phases, switching the pod at the
  start of each: write every quote (writer), check every quote (checker), rewrite the
  failures (writer), check them (checker), twice. The quote table lands in
  `data/processed/quotes/<run>/`. `scripts/quotes_variety.py` measures variety with
  Voyage. The export joins the quotes and goes to Hugging Face as usual.

## Once per account

**Secrets** (RunPod → Secrets):

| Secret | Holds |
|---|---|
| `HF_TOKEN` | existing; the pod downloads the models with it |
| `GITHUB_DATASETS_TOKEN` | GitHub fine-grained token `runpod-micromotives-datasets-read`: this repo only, Contents read-only. It expires, so renew it here when it does |
| `QUOTES_API_KEY` | **new**: any long random string, e.g. from `openssl rand -hex 24`. The same value goes in `~/.bash_profile` here as `export QUOTES_API_KEY=...` |

**Template** `micromotives-quotes` (RunPod → Templates):

- Image: the same `runpod/pytorch` image as training. vLLM is installed as its own tool
  with its own torch; the image only supplies a recent driver.
- Container disk 50 GB; volume 150 GB at `/workspace`, so the models (about 100 GB)
  download once and are kept while the pod is stopped.
- **Expose HTTP port 4000** (the router).
- Environment variables: `HF_TOKEN` = `{{ RUNPOD_SECRET_HF_TOKEN }}`,
  `GITHUB_DATASETS_TOKEN` = `{{ RUNPOD_SECRET_GITHUB_DATASETS_TOKEN }}` (alongside
  training's `GITHUB_TOKEN` when the template is shared), `QUOTES_API_KEY` = `{{ RUNPOD_SECRET_QUOTES_API_KEY }}`,
  `HF_HOME` = `/workspace/hf`.

## Each session

**1. Deploy** template `micromotives-quotes`, Secure Cloud, CUDA 13.0 and up, a GPU of
80 GB or more (the checker alone needs that much to run many checks at once; a 48 GB
card leaves it room for two or three). Which card, and its cost, is agreed with rich
before deploying. Or **Start** the stopped pod from last time.

**2. Connect** (Web Terminal) and paste:

```
cd /workspace
[ -d micromotives-datasets ] || git -c credential.helper='!f(){ echo username=x-access-token; echo password=$GITHUB_DATASETS_TOKEN; }; f' \
  clone https://github.com/richardhutton/micromotives-datasets.git
cd micromotives-datasets
git -c credential.helper='!f(){ echo username=x-access-token; echo password=$GITHUB_DATASETS_TOKEN; }; f' pull --ff-only
tmux kill-session -t serve 2>/dev/null; pkill -f "vllm serve"; pkill -f quotes_router
bash scripts/pod_serve_quotes.sh
```

It starts the router in a tmux session `serve`, and the router loads the writer. The
first time takes 20 to 30 minutes (download and load); after that, a few minutes. Ready
when `curl -s localhost:4000/health` shows `{"model": "writer", "status": "ready"}`. The
first switch to the checker downloads it too (about 62 GB); after that a switch takes a
few minutes.

**3. Run from here** (a batch, or `--resume` to carry on a stopped one):

```
source ~/.bash_profile
export QUOTES_URL=https://<pod id>-4000.proxy.runpod.net
T=data/processed/exports/v3/studies_10pct/train.parquet
uv run python scripts/quotes_run.py $T data/processed/quotes/full-2 --existing data/processed/quotes/full-1 --limit 10000
uv run python scripts/quotes_run.py $T data/processed/quotes/full-1 --resume
```

The run prints each phase, each switch (`pod: checker loading … ready`) and progress
with a time estimate. It saves after every phase; `--resume` carries on from the last
saved phase on the same rows. A request that fails is retried, and one that keeps
failing is counted in `run.json` (`request_failures`) rather than stopping the run. If a
model fails to start, the run stops and prints that model's last error line.

**4. Stop the pod** in the console when the batches are done (the volume keeps the
models for next time, about $0.70 a day); terminate it when quotes are finished.

**5. Export with quotes:**
`uv run python scripts/export.py v4 studies --fraction 0.1 --quotes data/processed/quotes/<run>`,
then upload as before.

## Notes

- RunPod's HTTPS proxy closes a request after about 100 seconds, which is why a writer
  call holds at most six rows. If `request_failures` shows many timeouts (`ReadTimeout`
  or `http 524`), lower `MAX_ITEMS` in `quotes_run.py`.
- Each model gets 0.90 of the GPU's memory while it is loaded; the writer has a 16,384
  token context and the checker 8,192 (one quote per check).

| Symptom | Fix |
|---|---|
| a switch reports `failed` | the run prints the error; the full log is `/workspace/serve/<writer or checker>.log` |
| checker never comes up | Gemma 4 or FP8-on-load unsupported by this vLLM: read `checker.log`, try the next release |
| `409 … switch first` | a request named the model that is not loaded; the runner switches before each phase, so this means two runs at once |
| `401` from the router | `QUOTES_API_KEY` here differs from the pod's secret |
| clone fails with 403 | `GITHUB_DATASETS_TOKEN` is missing from the template, misspelt, or expired |

One model at a time is not yet run on a pod. Here, against stand-in models, a run went
writer, checker, writer, checker, writer, checker with a stop and `--resume` in the
middle, and the router's switching, refusal of the other model and crash reporting are
tested (`tests/test_quotes_run.py`).
