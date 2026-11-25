import os, json, time, base64, wave, requests
from dotenv import load_dotenv

load_dotenv()
GEMINI_KEY = os.environ["GEMINI_API_KEY"]
CF_ACC, CF_TOKEN = os.environ["CF_ACCOUNT_ID"], os.environ["CF_API_TOKEN"]
os.makedirs("outputs/smoke", exist_ok=True)

def log(stage, model, params, start, ok, note=""):
    entry = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "stage": stage, "model": model,
             "params": params, "latency_s": round(time.time() - start, 2),
             "ok": ok, "cost_usd": 0.0, "note": note}
    with open("runs.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(entry)

def gemini_url(model):
    return f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_KEY}"
def post_with_retry(url, max_tries=5, **kwargs):
    """Retry on 429 (quota) and 5xx (server busy) with exponential backoff."""
    for attempt in range(1, max_tries + 1):
        r = requests.post(url, timeout=60, **kwargs)
        if r.status_code not in (429, 500, 502, 503, 504):
            return r
        if attempt == max_tries:
            break
        wait = 2 ** attempt  # 2, 4, 8, 16, 32 seconds
        print(f"  {r.status_code} on attempt {attempt}, retrying in {wait}s...")
        time.sleep(wait)
    return r

# 1. Gemini text, with fallback models if the main one is overloaded
models = [os.environ["GEMINI_TEXT_MODEL"]] + \
         [x for x in os.environ.get("GEMINI_TEXT_FALLBACKS", "").split(",") if x]
for m in models:
    t = time.time()
    r = post_with_retry(gemini_url(m), max_tries=3,
                        json={"contents": [{"parts": [{"text": "Say hello in Amharic in one sentence."}]}]})
    log("smoke_text", m, {}, t, r.ok, r.text[:200] if not r.ok else
        r.json()["candidates"][0]["content"]["parts"][0]["text"])
    if r.ok:
        break


# 2. Gemini TTS (returns raw 24 kHz 16-bit mono PCM)
m = os.environ["GEMINI_TTS_MODEL"]; t = time.time()
body = {"contents": [{"parts": [{"text": "ሰላም፣ ይህ የሙከራ ድምፅ ነው።"}]}],
        "generationConfig": {"responseModalities": ["AUDIO"],
            "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": "Kore"}}}}}
r = post_with_retry(gemini_url(m), json=body)
if r.ok:
    pcm = base64.b64decode(r.json()["candidates"][0]["content"]["parts"][0]["inlineData"]["data"])
    with wave.open("outputs/smoke/tts.wav", "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000); w.writeframes(pcm)
log("smoke_tts", m, {"voice": "Kore"}, t, r.ok, "" if r.ok else r.text[:200])

# 3. Cloudflare image
m = os.environ["CF_IMAGE_MODEL"]; t = time.time()
r = post_with_retry(f"https://api.cloudflare.com/client/v4/accounts/{CF_ACC}/ai/run/{m}",
                  headers={"Authorization": f"Bearer {CF_TOKEN}"},
                  json={"prompt": "warm hand-painted Ethiopian highland market at dawn", "steps": 4})
if r.ok:
    with open("outputs/smoke/image.jpg", "wb") as f:
        f.write(base64.b64decode(r.json()["result"]["image"]))
log("smoke_image", m, {"steps": 4}, t, r.ok, "" if r.ok else r.text[:200])
