# Costs

All stages ran on free tiers. Money spent: **$0.00**. The real constraints were quotas and rate limits, logged below.

Call counts come from `runs.jsonl`. Regenerate them with:
```powershell
python -c "import json,collections as c;n=c.Counter((j.get('stage'),j.get('model'),j.get('ok')) for j in map(json.loads,open('runs.jsonl',encoding='utf-8')));[print(f'{s!s:12} {m!s:45} ok={o!s:5} {k}') for (s,m,o),k in sorted(n.items(),key=str)]"
```

| Stage | Provider / model | Successful calls | Failed calls | Free-tier limit seen | Cost |
|---|---|---|---|---|---|
| Smoke test | Gemini text 3.8 / 3.7 / 3.5 Flash | [n] | [n] (503 high demand) | intermittent 503 on 3.8 and 3.7 | $0 |
| Smoke test | Cloudflare FLUX.1 schnell | [n] | 0 | | $0 |
| Narration | Gemini 3.8 Flash TTS | [n] | [n] (429) | 429 "exceeded your current quota" after about 8–9 requests [exact limit from AI Studio] | $0 |
| Narration | Gemini 2.5 Flash preview TTS (fallback) | [n] | [n] | | $0 |
| Keyframes | Cloudflare FLUX.2 [dev] | 12 (2 refs + 10 keyframes) [+ regenerations] | 0 | Workers AI daily free allocation [neurons used, from dashboard] | $0 |
| Motion | FFmpeg (local CPU) | 10 clips | 1 run (F7) | none | $0 |
| Score | ACE-Step on Kaggle T4 | [n] | [n] | Kaggle GPU 30 h/week; used [h] | $0 |
| Hero motion | Wan 2.2 on Kaggle T4 | [n] | [n] | Kaggle GPU 30 h/week; used [h] | $0 |
| Assembly | FFmpeg (local CPU) | [n] | [n] | none | $0 |

## Latency (from runs.jsonl)
- Gemini text: 10.3 s (3.5 Flash after two 503 fallbacks).
- Gemini TTS: about 4 s per line.
- FLUX.2 [dev] at 1360×768, 25 steps: 11–17 s per keyframe.
- Ken Burns: [seconds for all 10 clips on my laptop].
- Assembly: [seconds per format, from runs.jsonl `latency_s`].

## Lessons
- Caching saved the most quota: reruns after a storyboard edit regenerate only changed shots.
- A daily TTS quota means generating narration early in the day and keeping a fallback voice.
- Local FFmpeg stages (motion, assembly) cost nothing and can be rerun freely, so they absorb all the iteration.
