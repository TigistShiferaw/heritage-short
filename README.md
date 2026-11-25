# Three Cups (ሦስት ስኒ): a Heritage Short

An 80-second illustrated film about a grandmother's Ethiopian coffee ceremony, told through its three rounds: **abol**, **tona** and **bereka**. Amharic narration, English subtitles, made with an AI pipeline driven by one file: `storyboard.json`.

Built for the *AI-Content Generation: The Heritage Short* challenge (deadline 26 Nov 2026).

## Outputs

| File | What it is |
|---|---|
| `outputs/final/three_cups_16x9.mp4` | 1920×1080 film for Telegram and YouTube |
| `outputs/final/three_cups_9x16.mp4` | 1080×1920 film for TikTok and Instagram Reels |
| `outputs/final/subtitles_en.srt`, `subtitles_am.srt` | Soft subtitles (English, Amharic) |
| `outputs/keyframes/contact_sheet.jpg` | All 10 keyframes on one page |
| `outputs/radio_cut.mp4` | Phase 1 checkpoint: narration over a black screen |
| `outputs/rough_cut.mp4` | Phase 2 checkpoint: Ken Burns clips with narration, no subtitles |
| `runs.jsonl` | One line per model or FFmpeg call: stage, model, time, success, notes |

## Pipeline

```
storyboard.json ──validate.py──┬─ narration.py ─────── Gemini TTS ──────────► outputs/narration/*.wav
                               ├─ radio_cut.py ─────── FFmpeg ──────────────► outputs/radio_cut.mp4
                               ├─ keyframes.py ─────── Cloudflare FLUX.2 ───► outputs/characters, outputs/keyframes
                               ├─ motion_kenburns.py ─ FFmpeg pan/zoom ─────► outputs/motion/*.mp4
                               ├─ (Kaggle) Wan 2.2 ─── optional hero shots ─► outputs/wan/*.mp4
                               ├─ (Kaggle) ACE-Step ── score ───────────────► outputs/music/score.wav
                               └─ assemble.py ──────── FFmpeg + Pillow ─────► outputs/final/
```

Model stages cache their outputs by a hash of their inputs, so rerunning after a storyboard edit only regenerates the shots that changed. See [ARCHITECTURE.md](ARCHITECTURE.md).

## Setup (Windows, PowerShell)

1. Install Python 3.12 and FFmpeg (`winget install Gyan.FFmpeg`, then open a **new** terminal).
2. Create the environment:
   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
3. Create `.env` in the project root (never commit it):
   ```
   GEMINI_API_KEY=...
   GEMINI_TEXT_MODEL=gemini-3.8-flash
   GEMINI_TEXT_FALLBACKS=gemini-3.7-flash,gemini-3.5-flash
   GEMINI_TTS_MODEL=gemini-3.8-flash-tts
   GEMINI_TTS_FALLBACKS=gemini-2.5-flash-preview-tts
   CF_ACCOUNT_ID=...
   CF_API_TOKEN=...
   CF_IMAGE_MODEL=@cf/black-forest-labs/flux-1-schnell
   CF_KEYFRAME_MODEL=@cf/black-forest-labs/flux-2-dev
   KEYFRAME_STEPS=25
   KEYFRAME_BASE_SEED=1000
   ```
   The Gemini key comes from Google AI Studio, the Cloudflare token from the Cloudflare dashboard (Workers AI permission).
4. Check that every provider answers: `python pipeline\smoke_test.py`

## Run the film

```powershell
python pipeline\validate.py              # storyboard passes the schema, 60-90 s
python pipeline\narration.py             # Amharic narration, one WAV per shot
python pipeline\radio_cut.py             # optional: narration over black, for user testing
python pipeline\keyframes.py --refs-only # character references; review them first
python pipeline\keyframes.py             # 10 keyframes + contact sheet
python pipeline\motion_kenburns.py       # pan/zoom clip per shot
python pipeline\assemble.py              # both final films, subtitles, end card, ducked score
```

Optional GPU stages run on Kaggle (T4): ACE-Step for the score and Wan 2.2 for hero shots. Put their results in `outputs/music/score.wav` and `outputs/wan/<shot>.mp4`; `assemble.py` picks them up automatically.

To change one shot: edit it in `storyboard.json` (or add `"seed": 2001`), then rerun the stages. Unchanged shots print `cached`.

## Repository map

| Path | Purpose |
|---|---|
| `storyboard.json` | Single source of truth: shots, reasons, prompts, narration, music, end card |
| `schema/storyboard.schema.json` | JSON Schema the storyboard must pass |
| `pipeline/common.py` | `.env` loading, retry with backoff, model fallbacks, hashing, `runs.jsonl` logging |
| `pipeline/*.py` | One script per stage |
| `DESIGN.md` | Audience, intent, story, visual and sound design, user tests |
| `ARCHITECTURE.md` | How the pipeline works and why |
| `EXPERIMENTS.md` | What I tried, what happened, what I decided |
| `FAILURES.md` | What broke and how I fixed it |
| `COSTS.md` | Calls, quotas and money spent per stage |
| `ETHICS.md` | Consent, representation, AI disclosure, licences |

## AI disclosure

The pictures, motion, narration voice and music are AI-generated. The film ends on a card that says so and names the models. No real person's face or voice was used. See [ETHICS.md](ETHICS.md).
