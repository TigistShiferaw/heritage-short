import json, os, shutil, subprocess
from pathlib import Path

def find_ffmpeg():
    p = os.getenv("FFMPEG") or shutil.which("ffmpeg")
    if p:
        return p
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        raise SystemExit("ffmpeg not found. Install it (winget install Gyan.FFmpeg), "
                         "set FFMPEG=<full path> in .env, or pip install imageio-ffmpeg.")

FFMPEG = find_ffmpeg()
ROOT = Path(__file__).resolve().parents[1]
sb = json.loads((ROOT / "storyboard.json").read_text(encoding="utf-8"))
OUT = ROOT / "outputs" / "motion"
OUT.mkdir(parents=True, exist_ok=True)
FPS, W, H = 25, 1280, 720
MOVES = ["in", "left", "out", "right"]


for i, shot in enumerate(sb["shots"]):
    sid = shot["id"]
    dur = float(shot.get("duration_s") or shot.get("duration"))
    src = ROOT / "outputs" / "keyframes" / f"{sid}.png"
    dst = OUT / f"{sid}.mp4"
    if dst.exists() and dst.stat().st_mtime > src.stat().st_mtime:
        print(f"{sid}: cached"); continue
    n = int(round(dur * FPS))
    move = shot.get("move", MOVES[i % len(MOVES)])
    cx, cy = "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    if move == "in":
        z, x, y = f"1+0.12*on/{n}", cx, cy
    elif move == "out":
        z, x, y = f"1.12-0.12*on/{n}", cx, cy
    elif move == "left":
        z, x, y = "1.1", f"(iw-iw/zoom)*(1-on/{n})", cy
    else:
        z, x, y = "1.1", f"(iw-iw/zoom)*on/{n}", cy
    vf = (f"scale=5440:-2,zoompan=z='{z}':x='{x}':y='{y}':d={n}:s={W}x{H}:fps={FPS},"
          "format=yuv420p")
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", str(src), "-vf", vf,
                    "-frames:v", str(n), "-c:v", "libx264", "-crf", "18", str(dst)],
                   check=True)
    print(f"{sid}: {move} {dur}s -> {dst.name}")
