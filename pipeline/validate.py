"""Validate storyboard.json against the JSON Schema and check film length.
Run before every pipeline stage:  python pipeline/validate.py
"""
import json, sys
from jsonschema import Draft202012Validator

MIN_S, MAX_S = 60, 90

def load_storyboard(path="storyboard.json", schema_path="schema/storyboard.schema.json"):
    with open(schema_path, encoding="utf-8") as f:
        schema = json.load(f)
    with open(path, encoding="utf-8") as f:
        sb = json.load(f)

    errors = sorted(Draft202012Validator(schema).iter_errors(sb), key=lambda e: list(e.path))
    if errors:
        for e in errors:
            print(f"SCHEMA ERROR at {'/'.join(map(str, e.path)) or '(root)'}: {e.message}")
        sys.exit(1)

    ids = [s["id"] for s in sb["shots"]]
    if len(ids) != len(set(ids)):
        sys.exit("ERROR: duplicate shot ids")
    known = {c["id"] for c in sb["characters"]}
    for s in sb["shots"]:
        for c in s["characters"]:
            if c not in known:
                sys.exit(f"ERROR: shot {s['id']} uses unknown character '{c}'")

    total = sum(s["duration_s"] for s in sb["shots"]) + sb["end_card"]["duration_s"]
    if not MIN_S <= total <= MAX_S:
        sys.exit(f"ERROR: film is {total}s, must be {MIN_S}-{MAX_S}s")
    return sb, total

if __name__ == "__main__":
    sb, total = load_storyboard()
    print(f"OK: '{sb['title']}' - {len(sb['shots'])} shots, {total}s total")
