"""
Temporary script: send a hardcoded prompt straight to RunPod and save the result image.
Run from the project root:
    python test_prompt.py
"""
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
RUNPOD_API_KEY    = os.environ["RUNPOD_API_KEY"]
RUNPOD_ENDPOINT_ID = os.environ["RUNPOD_ENDPOINT_ID"]
BASE_URL = f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}"

# ── Prompt ────────────────────────────────────────────────────────────────────

POSITIVE_PROMPT = """w3t1nk Ukiyo-e sumi-e ink wash painting. A stoic orange tabby cat with rich ginger-orange fur marked by darker amber-brown tabby stripes, a pale cream muzzle, soft white fur along the inner chest and collar, small upright triangular ears, long white whiskers, a pink nose, and steady round teal-green eyes framed by small circular wire-rimmed reading glasses. Delicate brushstrokes render every stripe and whisker with expressive ink gradients.

The cat is portrayed as a noble scholar lord. It wears a richly layered formal kimono in deep crimson-red with dense gold arabesque patterns and scattered white sakura blossoms, rendered in intricate textile patterns with elegant linework. Wide floor-length sleeves, a structured pale gold inner under-robe visible at the open collar and cuffs, and a thick gold obi sash cinched at the waist. A tall rectangular black lacquered kammuri court hat sits upright on the head, thin black silk ribbon hanging from its rear. Refined outlines, stylized flat colors on the garments, subtle washi paper texture throughout.

The cat is seated upright on tatami flooring in a composed three-quarter pose, body turned slightly leftward toward a very low black lacquered writing table. The right forepaw actively grips and holds up the right edge of an unfurled paper scroll, paw clearly wrapped around the rolled end, raising it. The left forepaw is extended flat onto the table pressing down on the unrolled center of the scroll, actively reading it. The scroll is unfurled across the tabletop and clearly gripped and held in the right paw — this is the central action of the composition. The scroll surface is covered in neat vertical columns of Japanese calligraphy in soft ink wash. A rectangular black ink stone (suzuri) and a slender calligraphy brush rest in the upper-left corner of the table. The lower body and all hind legs are completely hidden beneath the heavy pooling kimono fabric spread across the tatami floor. The orange-striped tail curls from under the lower right hem, resting on the tatami. Refined composition, high detail.

To the right of the table stands a tall oval Japanese paper lantern (andon) on a black lacquer pedestal, emitting warm amber glow from its cream-white paper shade, soft layered washes of light. To the far left a small lacquered side table holds a slender ceramic vase with a single branch of white plum blossoms with red accents, rendered with delicate sumi-e brushwork.

The back wall shows a large ink wash sumi-e mural: jagged mountain peaks dissolving into billowing grey ink-wash clouds, dark silhouetted pine trees, and a large luminous full moon — a soft white disc — glowing in the upper center. Subtle ink gradients and expressive brushwork fill the background. On the left wall a vertical kakemono scroll painting in grey sumi-e ink. Two shoji screens with white rice-paper panels in dark wooden frames on the right. Tatami mat flooring with woven straw texture throughout.

Soft warm amber lantern light across the kimono and tabletop. Cool pale moonlight backlighting the room. Intimate, scholarly, noble, atmospheric mood. Decorative composition, expressive composition.

This is an artistic ink wash style painting, sumi-e aesthetic, delicate brushstrokes, subtle ink gradients, soft layered washes, refined composition, high detail, intricate textures, expressive composition. Traditional ukiyo-e style, Japanese woodblock print aesthetic, elegant linework, stylized flat colors, refined outlines, decorative composition, subtle washi paper texture, intricate textile patterns. No harness, no collar, no text, no watermark, no logos, no blur, no anatomical errors, no extra limbs."""

NEGATIVE_PROMPT = "blurry, watermark, deformed paws, human like fingers, extra limbs, bad anatomy"

JOB_INPUT = {
    "prompt":          POSITIVE_PROMPT,
    "negative_prompt": NEGATIVE_PROMPT,
    "lora_name":       "wetInkZTurbo.safetensors",
    "lora_strength":   0.3,
    "lora2_name":      "ukiyoeZTurbo.safetensors",
    "lora2_strength":  0.55,
    "width":           1216,
    "height":          832,
}

# ── RunPod helpers ────────────────────────────────────────────────────────────

def _req(method, path, body=None):
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(
        f"{BASE_URL}/{path}",
        data=data,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {RUNPOD_API_KEY}"},
        method=method,
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def run():
    print("Submitting job to RunPod…")
    resp = _req("POST", "run", {"input": JOB_INPUT})
    job_id = resp.get("id")
    if not job_id:
        sys.exit(f"No job ID returned: {resp}")
    print(f"Job ID: {job_id}")

    start = time.time()
    while True:
        elapsed = int(time.time() - start)
        s = _req("GET", f"status/{job_id}")
        status = s.get("status")
        print(f"  [{elapsed}s] {status}", end="\r")
        if status == "COMPLETED":
            print()
            return s.get("output", {})
        if status in ("FAILED", "CANCELLED"):
            sys.exit(f"\nJob ended: {status}\n{s}")
        if elapsed > 300:
            sys.exit("\nTimeout.")
        time.sleep(2)

# ── Main ──────────────────────────────────────────────────────────────────────

output = run()
images = output.get("images", [])

if not images:
    print("No images in output:")
    print(json.dumps(output, indent=2))
    sys.exit(1)

print(f"\nDone. {len(images)} image(s) returned.")
for i, img in enumerate(images):
    key = img.get("key", "")
    print(f"  [{i}] R2 key: {key}")

# Also print the seed so you can reproduce
print(f"Seed: {output.get('seed')}")
print("\nFull output:")
print(json.dumps(output, indent=2))
