# Architecture

## One contract: `storyboard.json`
Every stage reads the same file, and nothing else describes the film. It holds the title, style prompt, characters, optional prop references, music brief, the 8–12 shots and the end card. Each shot has an id, duration, the reason it exists, an image prompt, a motion prompt, its characters and props, the Amharic line with its English subtitle, and a music cue. Optional: `seed` (keyframe seed).

`pipeline/validate.py` checks it against `schema/storyboard.schema.json`: 8–12 shots, a reason per shot, Amharic text plus English subtitle, an end card containing "AI", and a total of 60–90 s. Run it before every stage.

## Stages

| Stage | Script | Model / tool | Output | Cache key |
|---|---|---|---|---|
| Full local pipeline | `pipeline/run_all.py` | Python subprocess runner | `outputs/final/*` | stage-specific |
| Smoke test | `smoke_test.py` | Gemini text, Gemini TTS, Cloudflare FLUX.1 schnell | `runs.jsonl` lines | none |
| Narration | `narration.py` | Gemini 3.8 Flash TTS (fallback 2.5 preview TTS), voice Kore | `outputs/narration/<shot>.wav` | text + voice + model actually used |
| Radio cut | `radio_cut.py` | FFmpeg | `outputs/radio_cut.mp4` | none (seconds to run) |
| Character refs | `keyframes.py --refs-only` | Cloudflare FLUX.2 [dev] | `outputs/characters/<id>.png` | description + style + seed + model |
| Keyframes | `keyframes.py` | FLUX.2 [dev] with character refs as input images | `outputs/keyframes/<shot>.png`, `contact_sheet.jpg` | prompt + seed + model + steps + size + reference file hashes |
| Motion | `motion_kenburns.py` | FFmpeg zoompan | `outputs/motion/<shot>.mp4` (1280×720) | none (local, fast) |
| Hero motion (optional) | Kaggle notebook | Wan 2.2 image-to-video | `outputs/wan/<shot>.mp4` | manual |
| Score | Kaggle notebook | ACE-Step 1.5 | `outputs/music/score.wav` | manual |
| Assembly | `assemble.py` | FFmpeg + libass + Pillow | `outputs/final/*` | none (rebuilt each run) |

## Shared helpers (`pipeline/common.py`)
- **Configuration:** keys and model names come from `.env`. Swapping a retired model is a one-line change (FAILURES.md F1).
- **Retries:** `post_with_retry()` retries 429 and 5xx with exponential backoff. It is the only place that calls `requests.post` (F3).
- **Fallback chains:** primary model plus fallbacks from `.env`, tried in order (F2, F5).
- **Caching:** a hash of each output's inputs is stored next to it; a rerun skips outputs whose inputs did not change (E2).
- **Logging:** one JSON line per call in `runs.jsonl`: time, stage, model, parameters, shot, seed, latency, success, note. COSTS.md and EXPERIMENTS.md are built from it.
- **FFmpeg:** found through the `FFMPEG` variable, then PATH, then `imageio-ffmpeg` (F7).

## Keyframes
FLUX.2 [dev] on Cloudflare takes multipart form data with `input_image_0..N`, each under 512×512, so generated character and prop references are made at 1024×1024 and sent as 496 px copies; a supplied `reference_image` can be used instead. A prop listed on a shot is passed as an image reference so its silhouette and material remain consistent. Shot seed = `shot.seed` if set, else `KEYFRAME_BASE_SEED + shot index`; character reference seed = base + 900 + index; prop reference seed = base + 950 + index. Changing one shot's seed or prompt regenerates only that shot.

## Timing and audio (`assemble.py`)
Shot start times are the running sum of `duration_s`. Gemini TTS `inlineData` can contain a WAV file (24 kHz, 16-bit, mono), not raw PCM. `narration.py` extracts the PCM samples before writing the canonical WAV and repairs older cached clips in place. Each narration line starts 0.5 s into its shot, fades in and out over 20 ms to avoid clicks, and is cut if it would overrun the shot (with a warning). Subtitles show from line start to line end plus 0.4 s (at least 2 s), never past the shot. The music bed is lowered by `music.duck_db` (−14 dB) whenever narration plays, using a volume envelope with 0.25 s ramps: an exact, documented duck instead of a compressor's variable one. The mix is normalised to −14 LUFS, true peak −1.5 dB.

## Two aspect ratios
Keyframes are generated once at 1360×768 and motion is rendered once at 16:9. Assembly normalises every clip to 1920×1080, 25 fps, exact shot length (padding with the last frame if a clip is short, e.g. a 5 s Wan clip in a 7 s shot), then concatenates. For 9:16 it places that film, scaled to 1080 wide, over a blurred copy filling 1080×1920 (or a centre crop with `--vertical crop`). Subtitles and end card are laid out per format. No extra model calls are needed for the second format.

## Why it is built this way
- **Cheap checkpoints first.** The radio cut tested story and pacing before any image was made; keyframes were reviewed on a contact sheet before any motion.
- **A guaranteed path plus optional upgrades.** Ken Burns motion and a placeholder drone always produce a complete, valid film. Wan 2.2 and ACE-Step run on a free GPU with quotas, so they are upgrades swapped in by dropping a file into a folder, not dependencies.
- **Free tiers are unreliable.** Every network call has retries, a fallback model, caching and a log line, so a failed run resumes without repeating rate-limited calls.
