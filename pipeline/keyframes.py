"""Stage: keyframes. Character reference sheets, then one keyframe per shot.
Model: FLUX.2 [dev] on Cloudflare Workers AI (supports seed, size and reference images).

Run:
  python pipeline/keyframes.py --refs-only     # 1. make and review character references
  python pipeline/keyframes.py                 # 2. make all keyframes (cached shots are skipped)
  python pipeline/keyframes.py --shots s03,s07 # only these shots

To redo a shot you dislike: give it a new "seed" in storyboard.json and rerun.
The hash changes, so only that shot is regenerated.
"""
import os, io, sys, time, base64, hashlib, argparse
from PIL import Image, ImageDraw
from validate import load_storyboard
from common import log, post_with_retry, input_hash, is_cached, mark_cached

ACCOUNT = os.environ["CF_ACCOUNT_ID"]
TOKEN = os.environ["CF_API_TOKEN"]
MODEL = os.environ.get("CF_KEYFRAME_MODEL", "@cf/black-forest-labs/flux-2-dev")
URL = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT}/ai/run/{MODEL}"
STEPS = int(os.environ.get("KEYFRAME_STEPS", "25"))
BASE_SEED = int(os.environ.get("KEYFRAME_BASE_SEED", "1000"))

W, H = 1360, 768        # 16:9 keyframe; the 9:16 version is a centre crop at assembly
REF_SIZE = 1024         # generated reference size
REF_INPUT = 496         # FLUX.2 on Workers AI needs reference inputs under 512x512
REF_DIR = "outputs/characters"
PROP_DIR = "outputs/props"
KF_DIR = "outputs/keyframes"

# Which look to use for each identity anchor. Shot prompts still set the age per shot.
REF_HINTS = {
    "grandmother": "shown at about 60 years old, a few silver strands in dark braided hair",
}


def flux(prompt, seed, w, h, refs=()):
    """Call FLUX.2 [dev]. It only accepts multipart form data, even for text-only prompts."""
    fields = {"prompt": (None, prompt), "steps": (None, str(STEPS)), "width": (None, str(w)),
              "height": (None, str(h)), "seed": (None, str(seed))}
    for i, path in enumerate(refs):
        with open(path, "rb") as f:
            fields[f"input_image_{i}"] = (os.path.basename(path), f.read(), "image/png")
    r = post_with_retry(URL, headers={"Authorization": f"Bearer {TOKEN}"}, files=fields, timeout=180)
    if r is None or not r.ok:
        return None, (r.text[:1000] if r is not None else "no response")
    body = r.json()
    b64 = body.get("result", body).get("image")
    if not b64:
        return None, f"no image in response: {str(body)[:300]}"
    return Image.open(io.BytesIO(base64.b64decode(b64))).convert("RGB"), ""


def file_hash(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]


def make_reference(char, sb, seed):
    """Front-facing portrait on a plain background, used as an identity anchor."""
    out = os.path.join(REF_DIR, f"{char['id']}.png")
    small = os.path.join(REF_DIR, f"{char['id']}_ref.png")
    prompt = (f"Character reference portrait. {char['description']} {REF_HINTS.get(char['id'], '')}. "
              f"Front view, full head and shoulders visible, calm expression, plain warm beige background, "
              f"even soft light, no other people. Style: {sb['style']['prompt']}. "
              f"Avoid: {sb['style'].get('negative', '')}")
    h = input_hash({"prompt": prompt, "seed": seed, "model": MODEL, "steps": STEPS, "size": REF_SIZE})
    if is_cached(out, h) and os.path.exists(small):
        print(f"ref {char['id']}: cached")
        return small
    t = time.time()
    img, err = flux(prompt, seed, REF_SIZE, REF_SIZE)
    log("keyframes-ref", MODEL, {"steps": STEPS, "size": REF_SIZE}, t, img is not None,
        shot=char["id"], seed=seed, note=err or "reference")
    if img is None:
        sys.exit(f"Reference for {char['id']} failed. See runs.jsonl.")
    img.save(out)
    img.resize((REF_INPUT, REF_INPUT), Image.LANCZOS).save(small)
    mark_cached(out, h)
    return small


def make_prop_reference(prop, sb, seed):
    """Make an isolated prop image to anchor its appearance across shots."""
    out = os.path.join(PROP_DIR, f"{prop['id']}.png")
    small = os.path.join(PROP_DIR, f"{prop['id']}_ref.png")
    prompt = (f"Object reference illustration of one {prop['description']}. "
              f"Show the complete object centered in a clear three-quarter view, "
              f"on a plain warm beige background, with no people, hands, cups or text. "
              f"Style: {sb['style']['prompt']}. Avoid: {sb['style'].get('negative', '')}")
    h = input_hash({"prompt": prompt, "seed": seed, "model": MODEL, "steps": STEPS, "size": REF_SIZE})
    if is_cached(out, h) and os.path.exists(small):
        print(f"prop {prop['id']}: cached")
        return small
    t = time.time()
    img, err = flux(prompt, seed, REF_SIZE, REF_SIZE)
    log("keyframes-prop", MODEL, {"steps": STEPS, "size": REF_SIZE}, t, img is not None,
        shot=prop["id"], seed=seed, note=err or "object reference")
    if img is None:
        sys.exit(f"Object reference for {prop['id']} failed. See runs.jsonl.")
    img.save(out)
    img.resize((REF_INPUT, REF_INPUT), Image.LANCZOS).save(small)
    mark_cached(out, h)
    return small


def keyframe_prompt(shot, sb):
    parts = [f"Style: {sb['style']['prompt']}.", f"Scene: {shot['image_prompt']}."]
    for i, c in enumerate(shot["characters"]):
        parts.append(f"The {c} must look like the reference in image {i}: same face, skin tone and "
                     f"clothing details, but at the age and pose described in the scene.")
    for i, prop in enumerate(shot.get("props", [])):
        ref_index = len(shot["characters"]) + i
        parts.append(f"The {prop} must match object reference image {ref_index} in silhouette, "
                     f"shape, proportions, material and color; do not redesign it.")
    parts.append("Keep the main subject inside the centre third of the frame; the film is also cropped to vertical.")
    if sb["style"].get("negative"):
        parts.append(f"Avoid: {sb['style']['negative']}.")
    return " ".join(parts)


def contact_sheet(sb):
    """One image with every keyframe, for quick review and for the report."""
    thumbs = []
    for s in sb["shots"]:
        p = os.path.join(KF_DIR, f"{s['id']}.png")
        if os.path.exists(p):
            im = Image.open(p).resize((340, 192))
            ImageDraw.Draw(im).text((8, 6), s["id"], fill="white")
            thumbs.append(im)
    if not thumbs:
        return
    cols = 5
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 340, rows * 192), "black")
    for i, im in enumerate(thumbs):
        sheet.paste(im, ((i % cols) * 340, (i // cols) * 192))
    sheet.save(os.path.join(KF_DIR, "contact_sheet.jpg"), quality=90)
    print(f"Contact sheet: {KF_DIR}/contact_sheet.jpg")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refs-only", action="store_true")
    ap.add_argument("--shots", default="", help="comma-separated shot ids, e.g. s03,s07")
    args = ap.parse_args()

    sb, _ = load_storyboard()
    os.makedirs(REF_DIR, exist_ok=True)
    os.makedirs(PROP_DIR, exist_ok=True)
    os.makedirs(KF_DIR, exist_ok=True)

    # 1. Character references (a hand-made reference_image in storyboard.json wins).
    refs = {}
    for i, char in enumerate(sb["characters"]):
        if char.get("reference_image"):
            refs[char["id"]] = char["reference_image"]
        else:
            refs[char["id"]] = make_reference(char, sb, BASE_SEED + 900 + i)
    prop_refs = {}
    for i, prop in enumerate(sb.get("props", [])):
        if prop.get("reference_image"):
            prop_refs[prop["id"]] = prop["reference_image"]
        else:
            prop_refs[prop["id"]] = make_prop_reference(prop, sb, BASE_SEED + 950 + i)
    if args.refs_only:
        print(f"References ready in {REF_DIR}/ and {PROP_DIR}/. Open them; if you dislike one, change "
              f"KEYFRAME_BASE_SEED in .env or the character description, then rerun.")
        return

    # 2. Keyframes.
    wanted = set(filter(None, args.shots.split(",")))
    made, failed = 0, []
    for idx, shot in enumerate(sb["shots"]):
        if wanted and shot["id"] not in wanted:
            continue
        out = os.path.join(KF_DIR, f"{shot['id']}.png")
        seed = shot.get("seed", BASE_SEED + idx)
        shot_props = [prop_refs[p] for p in shot.get("props", [])]
        shot_refs = [refs[c] for c in shot["characters"]] + shot_props
        prompt = keyframe_prompt(shot, sb)
        h = input_hash({"prompt": prompt, "seed": seed, "model": MODEL, "steps": STEPS,
                        "size": [W, H], "refs": [file_hash(p) for p in shot_refs]})
        if is_cached(out, h):
            print(f"{shot['id']}: cached")
            continue
        t = time.time()
        img, err = flux(prompt, seed, W, H, shot_refs)
        log("keyframes", MODEL, {"steps": STEPS, "size": [W, H], "refs": shot["characters"]}, t,
            img is not None, shot=shot["id"], seed=seed, note=err or "keyframe")
        if img is None:
            failed.append(shot["id"])
            continue
        img.save(out)
        mark_cached(out, h)
        made += 1

    contact_sheet(sb)
    print(f"Keyframes done: {made} generated, failed: {failed or 'none'}")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
