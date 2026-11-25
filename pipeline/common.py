"""Shared helpers for every pipeline stage: logging, retries, caching."""
import os, json, time, hashlib, requests
from dotenv import load_dotenv

load_dotenv()
RUNS_LOG = "runs.jsonl"


def log(stage, model, params, start, ok, shot=None, note="", seed=None, cost_usd=0.0):
    """Append one line per model call to runs.jsonl."""
    entry = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "stage": stage, "shot": shot,
             "model": model, "params": params, "seed": seed,
             "latency_s": round(time.time() - start, 2), "ok": ok,
             "cost_usd": cost_usd, "note": note}
    with open(RUNS_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"  [{stage}] {shot or ''} {model} ok={ok} {entry['latency_s']}s {note[:120]}")


def post_with_retry(url, max_tries=4, timeout=60, **kwargs):
    """Retry on 429 (quota) and 5xx (server busy) with exponential backoff."""
    for attempt in range(1, max_tries + 1):
        try:
            r = requests.post(url, timeout=timeout, **kwargs)
        except requests.RequestException as e:
            print(f"  network error on attempt {attempt}: {e}")
            r = None
        if r is not None and r.status_code not in (429, 500, 502, 503, 504):
            return r
        if attempt == max_tries:
            break
        wait = 2 ** attempt
        print(f"  {r.status_code if r is not None else 'error'} on attempt {attempt}, retrying in {wait}s...")
        time.sleep(wait)
    return r


def input_hash(inputs: dict) -> str:
    """Stable hash of everything that affects a stage's output."""
    blob = json.dumps(inputs, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:16]


def is_cached(out_path: str, h: str) -> bool:
    """True if the output exists and was made from exactly these inputs."""
    hash_file = out_path + ".hash"
    return os.path.exists(out_path) and os.path.exists(hash_file) and open(hash_file).read().strip() == h


def mark_cached(out_path: str, h: str):
    with open(out_path + ".hash", "w") as f:
        f.write(h)


def models_from_env(primary_var: str, fallback_var: str):
    """Primary model plus comma-separated fallbacks from .env."""
    return [os.environ[primary_var]] + [m for m in os.environ.get(fallback_var, "").split(",") if m]
