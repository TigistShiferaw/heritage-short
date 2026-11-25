"""Radio cut: narration over placeholder music on a black screen, timed by storyboard.json.
Used for user test 1 before any pictures exist.
Run:  python pipeline/radio_cut.py   ->  outputs/radio_cut.mp4
"""
import os, subprocess, shutil

import imageio_ffmpeg
from validate import load_storyboard

FFMPEG = shutil.which("ffmpeg") or imageio_ffmpeg.get_ffmpeg_exe()
TMP = "outputs/radio_tmp"
OUT = "outputs/radio_cut.mp4"
LEAD_IN_MS = 500  # small breath before each line


def run(args):
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", *args], check=True)


def main():
    sb, total = load_storyboard()
    os.makedirs(TMP, exist_ok=True)
    parts = []

    # 1. One audio segment per shot, padded or trimmed to the shot's exact duration.
    for shot in sb["shots"]:
        d = shot["duration_s"]
        src = f"outputs/narration/{shot['id']}.wav"
        seg = f"{TMP}/{shot['id']}.wav"
        if os.path.exists(src):
            run(["-i", src, "-af",
                 f"aresample=48000,adelay={LEAD_IN_MS}|{LEAD_IN_MS},apad,atrim=0:{d}",
                 "-ac", "2", seg])
        else:
            run(["-f", "lavfi", "-i", f"anullsrc=r=48000:cl=stereo", "-t", str(d), seg])
        parts.append(seg)

    # End card: silence for its duration.
    end_seg = f"{TMP}/end.wav"
    run(["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-t", str(sb["end_card"]["duration_s"]), end_seg])
    parts.append(end_seg)

    # 2. Join segments into one narration track.
    list_file = f"{TMP}/list.txt"
    with open(list_file, "w") as f:
        f.writelines(f"file '{os.path.basename(p)}'\n" for p in parts)
    narration = f"{TMP}/narration_full.wav"
    run(["-f", "concat", "-safe", "0", "-i", list_file, "-c", "copy", narration])

    # 3. Black video + narration + quiet placeholder drone (two soft sine tones).
    run(["-f", "lavfi", "-i", f"color=c=black:s=1280x720:r=24:d={total}",
         "-i", narration,
         "-f", "lavfi", "-i", f"sine=frequency=110:duration={total}",
         "-f", "lavfi", "-i", f"sine=frequency=165:duration={total}",
         "-filter_complex",
         "[2:a][3:a]amix=inputs=2,volume=0.06,afade=t=in:d=2,"
         f"afade=t=out:st={total - 3}:d=3[m];"
         "[1:a][m]amix=inputs=2:duration=first:normalize=0[a]",
         "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-shortest", OUT])
    print(f"Radio cut written: {OUT} ({total}s)")


if __name__ == "__main__":
    main()
