"""Stage: assembly. Builds the final 16:9 and 9:16 films from storyboard.json and earlier stage outputs.

Self-contained: needs only Pillow and FFmpeg (FFMPEG env var, PATH, or the imageio-ffmpeg package).

Inputs
  outputs/motion/<shot>.mp4          Ken Burns clips from motion_kenburns.py (any size, 16:9)
  outputs/wan/<shot>.mp4             optional Wan 2.2 clip; used instead of the Ken Burns clip
  outputs/narration/<shot>.wav       Amharic narration from narration.py
  outputs/music/score.(wav|mp3|flac) optional ACE-Step score; a quiet placeholder drone otherwise

Outputs (outputs/final/)
  three_cups_16x9.mp4   1920x1080, burned-in English subtitles, AI end card
  three_cups_9x16.mp4   1080x1920, same film centred on a blurred copy of itself
  subtitles_en.srt, subtitles_am.srt, mix.wav, end_card_*.png, subs_*.ass

Run from the project root:
  python pipeline\\assemble.py                 both formats
  python pipeline\\assemble.py --aspect 9x16   one format
  python pipeline\\assemble.py --vertical crop 9:16 by centre crop instead of blurred background
"""
import argparse, datetime, glob, json, os, shutil, subprocess, sys, time, wave
from PIL import Image, ImageDraw, ImageFont

FPS = 25
LEAD_S = 0.5            # breath before each narration line (same as the radio cut)
NARRATION_FADE_S = 0.02 # prevent clicks at the start and end of each voice clip
DUCK_RAMP_S = 0.25      # how fast the music dips and recovers
MUSIC_GAIN_DB = float(os.getenv("MUSIC_GAIN_DB", "-6"))
OUT_DIR = os.path.join("outputs", "final")
SLUG = os.getenv("FILM_SLUG", "three_cups")
ASPECTS = {"16x9": (1920, 1080), "9x16": (1080, 1920)}
# subtitle font size, side margin, bottom margin. 9:16 sits higher, above the TikTok/Reels buttons.
SUB_STYLE = {"16x9": (54, 160, 70), "9x16": (58, 80, 460)}
ETHIOPIC_FONTS = ["C:/Windows/Fonts/nyala.ttf", "C:/Windows/Fonts/ebrima.ttf",
                  "/usr/share/fonts/truetype/noto/NotoSansEthiopic-Regular.ttf"]
LATIN_FONTS = ["C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf",
               "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]


# ---------- helpers ----------
def find_ffmpeg():
    exe = os.getenv("FFMPEG") or shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        sys.exit("FFmpeg not found. Install it (winget install Gyan.FFmpeg) and open a new terminal.")


FFMPEG = find_ffmpeg()


def run(args, label):
    r = subprocess.run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", *args],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        log(label, False, r.stderr[-1000:])
        sys.exit(f"FFmpeg failed during {label}:\n{r.stderr[-2000:]}")


def log(step, ok, note, t0=None, extra=None):
    row = {"time": datetime.datetime.now().isoformat(timespec="seconds"), "stage": "assemble",
           "model": "ffmpeg", "step": step, "ok": ok, "note": note,
           "latency_s": round(time.time() - t0, 2) if t0 else None, "cost_usd": 0, **(extra or {})}
    with open("runs.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def wav_seconds(path):
    with wave.open(path) as w:
        return w.getnframes() / w.getframerate()


def load_font(candidates, size):
    for p in candidates:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    print("WARNING: no TrueType font found; the end card uses Pillow's default font")
    return ImageFont.load_default()


def load_storyboard():
    with open("storyboard.json", encoding="utf-8") as f:
        sb = json.load(f)
    total = sum(float(s["duration_s"]) for s in sb["shots"]) + float(sb["end_card"]["duration_s"])
    if not 60 <= total <= 90:
        sys.exit(f"Film is {total}s; it must be 60-90s. Run python pipeline\\validate.py")
    if "AI" not in sb["end_card"]["text"]:
        sys.exit("End card text must mention AI.")
    return sb, total


def build_timeline(sb):
    t, rows = 0.0, []
    for shot in sb["shots"]:
        d = float(shot["duration_s"])
        wav = os.path.join("outputs", "narration", f"{shot['id']}.wav")
        has = os.path.exists(wav)
        speech = wav_seconds(wav) if has else 0.0
        if not has:
            print(f"WARNING {shot['id']}: no narration WAV, shot will be silent")
        elif LEAD_S + speech > d:
            print(f"WARNING {shot['id']}: narration {speech:.1f}s does not fit in the {d:.0f}s shot; it is cut")
        end = t + LEAD_S + min(speech, d - LEAD_S)
        rows.append({"shot": shot, "start": t, "dur": d, "wav": wav if has else None,
                     "speech_start": t + LEAD_S, "speech_end": end,
                     "sub_start": t + LEAD_S, "sub_end": min(max(end, t + LEAD_S + 2.0) + 0.4, t + d - 0.05)})
        t += d
    return rows, t


# ---------- subtitles ----------
def srt_time(s):
    ms = int(round(s * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def ass_time(s):
    cs = int(round(s * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def write_srt(rows, key, path):
    n, out = 0, []
    for r in rows:
        text = r["shot"]["narration"][key].strip()
        if text:
            n += 1
            out.append(f"{n}\n{srt_time(r['sub_start'])} --> {srt_time(r['sub_end'])}\n{text}\n")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out))


def write_ass(rows, aspect, path):
    W, H = ASPECTS[aspect]
    size, side, bottom = SUB_STYLE[aspect]
    lines = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}",
             "WrapStyle: 0", "ScaledBorderAndShadow: yes", "", "[V4+ Styles]",
             "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
             "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, "
             "Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
             f"Style: Default,Arial,{size},&H00FFFFFF,&H000000FF,&H00101010,&H80000000,"
             f"-1,0,0,0,100,100,0,0,1,3,1,2,{side},{side},{bottom},1", "", "[Events]",
             "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    for r in rows:
        text = r["shot"]["narration"]["english"].strip().replace("{", "(").replace("}", ")")
        if text:
            lines.append(f"Dialogue: 0,{ass_time(r['sub_start'])},{ass_time(r['sub_end'])},Default,,0,0,0,,{text}")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


# ---------- end card ----------
def wrap(draw, text, fnt, max_w):
    lines, cur = [], ""
    for w in text.split():
        test = f"{cur} {w}".strip()
        if draw.textlength(test, font=fnt) <= max_w or not cur:
            cur = test
        else:
            lines.append(cur)
            cur = w
    return lines + ([cur] if cur else [])


def make_end_card(sb, aspect, path):
    W, H = ASPECTS[aspect]
    img = Image.new("RGB", (W, H), (30, 20, 13))
    d = ImageDraw.Draw(img)
    unit = min(W, H)
    title_f = load_font(ETHIOPIC_FONTS, int(unit * 0.075))
    body_f = load_font(LATIN_FONTS, int(unit * 0.042))
    blocks = [(wrap(d, sb["title"], title_f, W * 0.85), title_f, (240, 214, 170)),
              (wrap(d, sb["end_card"]["text"], body_f, W * 0.8), body_f, (235, 230, 220))]
    gap = int(unit * 0.06)
    heights = [len(ls) * int(f.size * 1.4) for ls, f, _ in blocks]
    y = (H - sum(heights) - gap) // 2
    for (ls, f, colour), h in zip(blocks, heights):
        for line in ls:
            d.text(((W - d.textlength(line, font=f)) / 2, y), line, font=f, fill=colour)
            y += int(f.size * 1.4)
        y += gap
    img.save(path)


# ---------- audio ----------
def find_music(override):
    if override:
        return override
    for p in sorted(glob.glob(os.path.join("outputs", "music", "score.*"))):
        if p.lower().endswith((".wav", ".flac", ".mp3", ".m4a", ".ogg")):
            return p
    return None


def duck_expression(rows, duck_db):
    """1.0 normally, duck gain while narration plays, with linear ramps in and out."""
    g, k, parts = 10 ** (duck_db / 20), DUCK_RAMP_S, []
    for r in rows:
        if r["wav"]:
            a, b = r["speech_start"], r["speech_end"]
            parts.append(f"clip((t-{a - k:.3f})/{k},0,1)*clip(({b + k:.3f}-t)/{k},0,1)")
    if not parts:
        return "1"
    expr = parts[0]
    for p in parts[1:]:
        expr = f"max({expr},{p})"
    return f"1-{1 - g:.4f}*{expr}"


def build_mix(sb, rows, total, music_override):
    out = os.path.join(OUT_DIR, "mix.wav")
    music = find_music(music_override)
    args, filters, labels = [], [], []
    for r in rows:
        if r["wav"]:
            i = len(labels)
            args += ["-i", r["wav"]]
            clip_duration = r["speech_end"] - r["speech_start"]
            fade_s = min(NARRATION_FADE_S, clip_duration / 2)
            filters.append(f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo,"
                           f"atrim=0:{clip_duration:.3f},"
                           f"afade=t=in:d={fade_s:.3f},"
                           f"afade=t=out:st={clip_duration - fade_s:.3f}:d={fade_s:.3f},"
                           f"adelay={int(round(r['speech_start'] * 1000))}:all=1[n{i}]")
            labels.append(f"[n{i}]")
    m = len(labels)
    if music:
        args += ["-stream_loop", "-1", "-i", music]
        src = f"[{m}:a]aresample=48000,aformat=channel_layouts=stereo,volume={MUSIC_GAIN_DB}dB"
    else:
        print("No outputs/music/score.* found: using the quiet placeholder drone")
        args += ["-f", "lavfi", "-i", f"aevalsrc=0.05*sin(2*PI*110*t)+0.04*sin(2*PI*165*t):s=48000:d={total}"]
        src = f"[{m}:a]aformat=channel_layouts=stereo"
    duck_db = sb["music"].get("duck_db", -14)
    filters.append(f"{''.join(labels)}amix=inputs={m}:normalize=0:duration=longest,"
                   f"apad=whole_dur={total},atrim=0:{total}[narr]")
    filters.append(f"{src},atrim=0:{total},volume='{duck_expression(rows, duck_db)}':eval=frame,"
                   f"afade=t=in:d=1.5,afade=t=out:st={total - 3}:d=3[mus]")
    filters.append("[narr][mus]amix=inputs=2:normalize=0:duration=first,"
                   "loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[a]")
    run([*args, "-filter_complex", ";".join(filters), "-map", "[a]", "-t", str(total),
         "-c:a", "pcm_s16le", out], "audio mix")
    return out, music or "placeholder drone"


# ---------- video ----------
def clip_for(sid):
    for p in (os.path.join("outputs", "wan", f"{sid}.mp4"),
              os.path.join("outputs", "motion", f"{sid}.mp4"),
              os.path.join("outputs", "motion", "16x9", f"{sid}.mp4")):
        if os.path.exists(p):
            return p
    sys.exit(f"No clip for {sid}. Run: python pipeline\\motion_kenburns.py")


def build_film(sb, rows, shots_total, aspect, mix, vertical):
    W, H = ASPECTS[aspect]
    ec_png = os.path.join(OUT_DIR, f"end_card_{aspect}.png")
    ass = os.path.join(OUT_DIR, f"subs_{aspect}.ass")
    make_end_card(sb, aspect, ec_png)
    write_ass(rows, aspect, ass)
    ec_dur = float(sb["end_card"]["duration_s"])
    BW, BH = 1920, 1080  # every shot is first normalised to 16:9 1080p
    args, filters, sources = [], [], []
    for i, r in enumerate(rows):
        src = clip_for(r["shot"]["id"])
        sources.append(f"{r['shot']['id']}={'wan' if os.sep + 'wan' + os.sep in src else 'kenburns'}")
        args += ["-i", src]
        filters.append(f"[{i}:v]fps={FPS},scale={BW}:{BH}:force_original_aspect_ratio=increase,crop={BW}:{BH},"
                       f"setsar=1,tpad=stop_mode=clone:stop_duration={r['dur']},trim=duration={r['dur']},"
                       f"setpts=PTS-STARTPTS,format=yuv420p[v{i}]")
    n = len(rows)
    filters.append(f"{''.join(f'[v{i}]' for i in range(n))}concat=n={n}:v=1:a=0[shots]")
    if aspect == "16x9":
        filters.append("[shots]null[framed]")
    elif vertical == "crop":
        filters.append(f"[shots]scale=-2:{H},crop={W}:{H},setsar=1[framed]")
    else:  # blurred copy behind, full 16:9 frame in the middle; nothing is cut off
        filters.append(f"[shots]split[bg0][fg0];"
                       f"[bg0]scale=-2:{H},crop={W}:{H},setsar=1,boxblur=30:3,eq=brightness=-0.08[bg];"
                       f"[fg0]scale={W}:-2[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1[framed]")
    args += ["-loop", "1", "-framerate", str(FPS), "-t", str(ec_dur), "-i", ec_png, "-i", mix]
    filters.append(f"[{n}:v]scale={W}:{H},setsar=1,format=yuv420p,fade=t=in:st=0:d=0.6[ve]")
    filters.append(f"[framed][ve]concat=n=2:v=1:a=0,fade=t=in:st=0:d=0.8,"
                   f"subtitles=filename={ass.replace(os.sep, '/')}[v]")
    out = os.path.join(OUT_DIR, f"{SLUG}_{aspect}.mp4")
    run([*args, "-filter_complex", ";".join(filters), "-map", "[v]", "-map", f"{n + 1}:a",
         "-t", str(shots_total + ec_dur), "-c:v", "libx264", "-crf", "20", "-preset", "medium",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out], f"{aspect} film")
    return out, sources


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--aspect", choices=["16x9", "9x16", "both"], default="both")
    ap.add_argument("--vertical", choices=["blur", "crop"], default=os.getenv("VERTICAL_MODE", "blur"))
    ap.add_argument("--music", help="music file to use instead of outputs/music/score.*")
    a = ap.parse_args()
    aspects = list(ASPECTS) if a.aspect == "both" else [a.aspect]

    sb, film_total = load_storyboard()
    os.makedirs(OUT_DIR, exist_ok=True)
    rows, shots_total = build_timeline(sb)
    write_srt(rows, "english", os.path.join(OUT_DIR, "subtitles_en.srt"))
    write_srt(rows, "text", os.path.join(OUT_DIR, "subtitles_am.srt"))

    t0 = time.time()
    mix, music = build_mix(sb, rows, film_total, a.music)
    log("mix", True, f"{film_total}s mix, music={music}", t0, {"duck_db": sb["music"].get("duck_db", -14)})
    print(f"Audio mix: {mix}  (music: {music})")

    for aspect in aspects:
        t0 = time.time()
        out, sources = build_film(sb, rows, shots_total, aspect, mix, a.vertical)
        log(f"film_{aspect}", True, out, t0, {"clips": sources, "vertical": a.vertical})
        print(f"{aspect}: {out}  ({film_total:.0f}s, {time.time() - t0:.0f}s to render)")
    print("Done. Check: python -c \"print(open('outputs/final/subtitles_en.srt',encoding='utf-8').read())\"")


if __name__ == "__main__":
    main()
