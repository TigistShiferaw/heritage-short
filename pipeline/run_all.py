"""Run the complete local pipeline from storyboard validation to final exports."""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PIPELINE = ROOT / "pipeline"
STAGES = [
    ("Validate storyboard", ["validate.py"]),
    ("Generate narration", ["narration.py"]),
    ("Generate character references", ["keyframes.py", "--refs-only"]),
    ("Generate keyframes", ["keyframes.py"]),
    ("Render motion clips", ["motion_kenburns.py"]),
    ("Assemble final films", ["assemble.py"]),
]


def main():
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    for label, args in STAGES:
        print(f"\n== {label} ==", flush=True)
        result = subprocess.run(
            [sys.executable, str(PIPELINE / args[0]), *args[1:]],
            cwd=ROOT,
            env=env,
        )
        if result.returncode:
            raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
