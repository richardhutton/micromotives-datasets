# Pod snippets

Copy and paste these into the quotes pod's Web Terminal. The full setup is in
`docs/RUNPOD_QUOTES.md`.

## Start serving (after starting or deploying the pod)

```
cd /workspace
[ -d micromotives-datasets ] || git -c credential.helper='!f(){ echo username=x-access-token; echo password=$GITHUB_DATASETS_TOKEN; }; f' \
  clone https://github.com/richardhutton/micromotives-datasets.git
cd micromotives-datasets
git -c credential.helper='!f(){ echo username=x-access-token; echo password=$GITHUB_DATASETS_TOKEN; }; f' pull --ff-only
tmux kill-session -t serve 2>/dev/null; pkill -f "vllm serve"; pkill -f quotes_router
bash scripts/pod_serve_quotes.sh
```

This works on a fresh pod and on a restarted one. Then send the pod ID to Claude.

## Is it up?

```
curl -s localhost:4000/health; echo
```

`{"model": "writer", "status": "ready"}` means ready. `loading` means wait, and `failed` means
paste the next command's output to Claude.

## What went wrong

```
curl -s localhost:4000/admin/state -H "Authorization: Bearer $QUOTES_API_KEY"; echo
tail -n 20 /workspace/serve/writer.log
tail -n 20 /workspace/serve/checker.log
```

## Watch it work

```
du -sh /workspace/hf                                  # model downloads (writer ~29 GB, checker ~62 GB)
grep "throughput" /workspace/serve/writer.log | tail -n 1
grep "throughput" /workspace/serve/checker.log | tail -n 1
```

## When it's finished

Stop the pod in the RunPod console when a run is done. Use Terminate instead if you won't be
back within about a day, because the volume costs about $0.87 a day.
