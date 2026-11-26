"""Stage: narration. Reads storyboard.json, writes outputs/narration/<shot>.wav.
Only shots whose narration text, voice or model changed are regenerated.
Run:  python pipeline/narration.py
"""
import io, os, sys, time, base64, wave
from validate import load_storyboard
from common import log, post_with_retry, input_hash, is_cached, mark_cached, models_from_env

OUT_DIR = "outputs/narration"
GEMINI_KEY = os.environ["GEMINI_API_KEY"]


def tts(text, voice, model):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_KEY}"
    body = {"contents": [{"parts": [{"text": text}]}],
            "generationConfig": {"responseModalities": ["AUDIO"],
                                 "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}}}}
    return post_with_retry(url, json=body, timeout=120)


def decode_pcm(audio):
    if audio.startswith(b"RIFF"):
        if audio[8:12] != b"WAVE":
            raise ValueError("TTS audio has a RIFF header but is not a WAV file")
        with wave.open(io.BytesIO(audio), "rb") as source:
            if (source.getnchannels(), source.getsampwidth(), source.getframerate()) != (1, 2, 24000):
                raise ValueError("TTS WAV must be 24 kHz, 16-bit, mono PCM")
            audio = source.readframes(source.getnframes())
    if not audio or len(audio) % 2:
        raise ValueError("TTS PCM must contain a non-empty, even number of bytes")
    return audio


def save_wav(path, audio):
    pcm = decode_pcm(audio)
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000); w.writeframes(pcm)
    return len(pcm) / (2 * 24000)  # seconds


def repair_cached_wav(path):
    with wave.open(path, "rb") as source:
        if (source.getnchannels(), source.getsampwidth(), source.getframerate()) != (1, 2, 24000):
            raise ValueError(f"{path} must be 24 kHz, 16-bit, mono PCM")
        audio = source.readframes(source.getnframes())
    pcm = decode_pcm(audio)
    if pcm != audio:
        save_wav(path, pcm)


def main():
    sb, _ = load_storyboard()
    os.makedirs(OUT_DIR, exist_ok=True)
    voice = sb["narration_voice"]
    models = models_from_env("GEMINI_TTS_MODEL", "GEMINI_TTS_FALLBACKS")
    pause = float(os.environ.get("TTS_PAUSE_S", "7"))  # stay under free-tier requests/minute
    regenerated, failed, fallback_used = 0, [], []

    for shot in sb["shots"]:
        text = shot["narration"]["text"].strip()
        out = os.path.join(OUT_DIR, f"{shot['id']}.wav")
        if not text:
            print(f"{shot['id']}: no narration, skipped")
            continue
        h = input_hash({"text": text, "voice": voice, "model": models[0]})
        if is_cached(out, h):
            repair_cached_wav(out)
            print(f"{shot['id']}: cached")
            continue

        if regenerated:
            time.sleep(pause)
        for model in models:
            t = time.time()
            r = tts(text, voice, model)
            if r is not None and r.ok:
                pcm = base64.b64decode(r.json()["candidates"][0]["content"]["parts"][0]["inlineData"]["data"])
                secs = save_wav(out, pcm)
                # Cache under the model actually used: a fallback clip is retried with the
                # primary model on the next run, so every line ends up in the same voice.
                mark_cached(out, input_hash({"text": text, "voice": voice, "model": model}))
                if model != models[0]:
                    fallback_used.append(shot["id"])
                note = f"{secs:.1f}s audio"
                if secs > shot["duration_s"]:
                    note += f" WARNING longer than shot ({shot['duration_s']}s)"
                log("narration", model, {"voice": voice, "chars": len(text)}, t, True, shot=shot["id"], note=note)
                regenerated += 1
                break
            err = r.text[:1000] if r is not None else "no response"
            log("narration", model, {"voice": voice}, t, False, shot=shot["id"], note=err)
        else:
            failed.append(shot["id"])

    print(f"Narration done: {regenerated} regenerated, failed: {failed or 'none'}, "
          f"fallback voice (rerun later): {fallback_used or 'none'}")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
