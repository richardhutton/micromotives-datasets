# Writing quotes with models on RunPod

The models run on a RunPod pod behind one router; everything else runs here. Design:
`docs/QUOTES_SPEC.md`.

- **On the pod:** the writer (Qwen3.8-27B FP8) and the checker (Gemma 4 31B, quantised
  to FP8 on load) served by vLLM, and a small router in front
  (`scripts/quotes_router.py`). The router sends each request to the model it names,
  `writer` or `checker`, on one address that needs an API key.
- **Here:** `scripts/quotes_run.py` sends the rows, in phases: write every quote, check
  every quote, rewrite the duds, check them again. The quote table lands in
  `data/processed/quotes/<run>/`. `scripts/quotes_variety.py` measures variety with
  Voyage. The export joins the quotes and goes to Hugging Face as usual.

## Once per account

**Secrets** (RunPod → Secrets):

| Secret | Holds |
|---|---|
| `HF_TOKEN` | existing; the pod downloads the models with it |
| `GITHUB_DATASETS_TOKEN` | GitHub fine-grained token `runpod-micromotives-datasets-read`: this repo only, Contents read-only. It expires, so renew it here when it does |
| `RUNPOD_QUOTES_API_KEY` | **new**: any long random string, e.g. from `openssl rand -hex 24`. The same value goes in `~/.bash_profile` here as `export RUNPOD_QUOTES_API_KEY=...` |

**Template** `micromotives-quotes` (RunPod → Templates):

- Image: the same `runpod/pytorch` image as training. vLLM is installed as its own tool
  with its own torch; the image only supplies a recent driver.
- Container disk 50 GB; volume 150 GB at `/workspace`, so the models (about 100 GB)
  download once and are kept while the pod is stopped.
- **Expose HTTP port 4000** (the router).
- Environment variables: `HF_TOKEN` = `{{ RUNPOD_SECRET_HF_TOKEN }}`,
  `GITHUB_DATASETS_TOKEN` = `{{ RUNPOD_SECRET_GITHUB_DATASETS_TOKEN }}` (alongside
  training's `GITHUB_TOKEN` when the template is shared), `RUNPOD_QUOTES_API_KEY` = `{{ RUNPOD_SECRET_RUNPOD_QUOTES_API_KEY }}`,
  `HF_HOME` = `/workspace/hf`.

## Each session

**1. Deploy** template `micromotives-quotes`, Secure Cloud, CUDA 13.0 and up, GPU
**H100 80 GB** (both models side by side). Or **Start** the stopped pod from last time.

**2. Connect** (Web Terminal) and paste:

```
cd /workspace
[ -d micromotives-datasets ] || git -c credential.helper='!f(){ echo username=x-access-token; echo password=$GITHUB_DATASETS_TOKEN; }; f' \
  clone https://github.com/richardhutton/micromotives-datasets.git
cd micromotives-datasets
bash scripts/pod_serve_quotes.sh
```

It starts the writer, then the checker, then the router, in a tmux session `serve`.
The first time takes 20 to 30 minutes (download and load); after that, a few minutes.
It is ready when `https://<pod id>-4000.proxy.runpod.net/health` shows both `true`.

**3. Run batches from here:**

```
source ~/.bash_profile
export QUOTES_URL=https://<pod id>-4000.proxy.runpod.net
uv run python scripts/quotes_pilot_rows.py data/processed/exports/v3/studies_10pct/train.parquet
for s in sampling angle_voice full_persona group; do
  uv run python scripts/quotes_run.py data/processed/exports/v3/studies_10pct/train.parquet \
    data/processed/quotes/pilot-$s --setting $s --keys data/processed/quotes/pilot_keys.parquet
  uv run python scripts/quotes_variety.py data/processed/exports/v3/studies_10pct/train.parquet \
    data/processed/quotes/pilot-$s
done
```

Each run saves after every phase, so a run that stops part-way keeps what it paid for;
rerun with `--existing <run folder>` to carry on from its passed quotes. A request that
fails is retried, and one that keeps failing is counted in `run.json`
(`request_failures`) rather than stopping the run.

**4. Stop the pod** in the console when the batches are done (the volume keeps the
models for next time, about $0.70 a day); terminate it when quotes are finished.

**5. Export with quotes:**
`uv run python scripts/export.py v4 studies --fraction 0.1 --quotes data/processed/quotes/<run>`,
then upload as before.

## Notes

- RunPod's HTTPS proxy closes a request after about 100 seconds, which is why a writer
  call holds at most six rows. If `request_failures` shows many timeouts (`ReadTimeout`
  or `http 524`), lower `MAX_ITEMS` in `quotes_run.py`.
- Each vLLM server gets 0.45 of the H100's memory, with a 16,384-token context.

| Symptom | Fix |
|---|---|
| `/health` shows a model `false` | `tmux attach -t serve`; read `/workspace/serve/<writer or checker>.log` |
| checker never comes up | Gemma 4 or FP8-on-load unsupported by this vLLM: read `checker.log`, try the next release |
| `the pod is not serving 'writer'` | the router started before a model; restart `pod_serve_quotes.sh` |
| `401` from the router | `RUNPOD_QUOTES_API_KEY` here differs from the pod's secret |
| clone fails with 403 | `GITHUB_DATASETS_TOKEN` is missing from the template, misspelt, or expired |

Not yet run on a pod: the first pilot is the test of `pod_serve_quotes.sh`. The runner,
router and variety script have been run end to end here against stand-in models.
