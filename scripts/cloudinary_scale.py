"""
RationSeva - Weighing-scale photo reader (Cloudinary OCR)
=========================================================

Beneficiary photographs the weighing-scale display while collecting ration.
Cloudinary's OCR add-on (Google Vision) reads the digits, we compare the
reading with the entitlement, and if it's short we create complaint evidence:
a stamped photo + the numbers. Ambiguous readings (product/label text, several
plausible numbers) come back UNREADABLE instead of being guessed.

Needs: Cloudinary "OCR Text Detection and Extraction" add-on (free plan).

Usage:
    python cloudinary_scale.py scale.jpg --fps 0306122 --expected-kg 35
    python cloudinary_scale.py scale.jpg --fps 0306122 --expected-kg 35 --commodity Rice --tolerance-kg 0.1
"""

import argparse
import json
import re

from cloudinary_proof import configure, proof_from_incoming, upload_proof

NUM_RE = re.compile(r"(\d{1,3}(?:[.,]\d{1,3})?)\s*(kg|kgs|g|gm|gms)?\b", re.I)

# lines that are product descriptions / specs, not a live reading
IGNORED_LINE_RE = re.compile(
    r"\b(max|min|capacity|cap|model|serial|mercadolibre|amazon|"
    r"price|product|kitchen scale|unit|resolution|division)\b",
    re.I,
)

UNREADABLE_MSG = "Couldn't read a valid weight. Please retake the photo or enter the weight manually."


def ocr_text(cloudinary_response):
    """Full text Google Vision found in the image ('' if nothing / add-on missing)."""
    ocr = (cloudinary_response.get("info") or {}).get("ocr", {}).get("adv_ocr", {})
    if ocr.get("status") != "complete":
        return None, ocr.get("status", "not_requested")
    try:
        return ocr["data"][0]["textAnnotations"][0]["description"], "complete"
    except (KeyError, IndexError, TypeError):
        return "", "complete"


def pick_weight_kg(text):
    """
    Conservatively pick the scale reading from OCR text.
    Skips product/spec lines, printed labels ("30kg max", "e=5g") and model codes ("DS-252"),
    and needs a decimal point or a unit. Returns (kg, raw_match) only when exactly one
    plausible candidate is left, else (None, None) - we don't guess.
    """
    if not text:
        return None, None
    candidates = []
    for line in text.splitlines():
        line = line.strip()
        if not line or IGNORED_LINE_RE.search(line):
            continue
        in_line = []
        for m in NUM_RE.finditer(line):
            raw, unit = m.group(1), (m.group(2) or "").lower()
            # printed labels on the scale body, not the reading: "Min 100g", "e=5g", "d=1g"
            around = line[max(0, m.start() - 6):m.end() + 6].lower()
            if re.search(r"e\s*=|d\s*=", around):
                continue
            # part of a model/serial code like "DS-252" or "A12"
            prev = line[m.start() - 1] if m.start() > 0 else " "
            if prev.isalpha() or prev == "-":
                continue
            if "." not in raw and "," not in raw and not unit:
                continue
            value = float(raw.replace(",", "."))
            if unit in ("g", "gm", "gms"):
                value /= 1000.0
            if not 0 < value <= 100:          # ration loads are a few kg to ~50 kg
                continue
            in_line.append((round(value, 3), m.group(0).strip()))
        if len(in_line) == 1:                 # several numbers on one line -> don't guess
            candidates += in_line
    if len(candidates) != 1:
        return None, None
    return candidates[0]


def check_scale(image, fps_id, expected_kg, commodity=None, tolerance_kg=0.1, lat=None, lng=None):
    proof = upload_proof(image, fps_id, "weighing", lat, lng,
                         note=f"{commodity or 'ration'} expected {expected_kg} kg",
                         ocr="adv_ocr")
    return scale_verdict(proof, expected_kg, commodity, tolerance_kg)


def check_scale_incoming(public_id, fps_id, expected_kg, commodity=None, tolerance_kg=0.1, lat=None, lng=None):
    """Same as check_scale, for a photo already uploaded with the signed Upload Widget."""
    proof = proof_from_incoming(public_id, fps_id, "weighing", lat, lng,
                                note=f"{commodity or 'ration'} expected {expected_kg} kg")
    return scale_verdict(proof, expected_kg, commodity, tolerance_kg)


def scale_verdict(proof, expected_kg, commodity, tolerance_kg):
    raw = proof.pop("_raw", {})
    text, status = ocr_text(raw)
    reading, matched = pick_weight_kg(text)

    if status != "complete":
        verdict, message = "OCR_UNAVAILABLE", f"OCR status: {status}. Is the OCR add-on enabled?"
    elif reading is None or reading <= 0:
        # never SHORT_WEIGHT on a 0 / missing reading
        verdict, message = "UNREADABLE", UNREADABLE_MSG
    elif reading > expected_kg * 1.5 and reading > expected_kg + 2:
        # way over entitlement -> more likely a misread / wrong photo than generous dealer
        verdict, message = "NEEDS_REVIEW", (f"Reading {reading} kg is far above entitlement {expected_kg} kg - "
                                            "possible misread or wrong photo. Please retake or enter weight manually.")
    elif reading + tolerance_kg < expected_kg:
        short = expected_kg - reading
        verdict, message = "SHORT_WEIGHT", f"Scale shows {reading} kg, entitled {expected_kg} kg -> short by {short:.2f} kg"
    else:
        verdict, message = "OK", f"Scale shows {reading} kg, entitled {expected_kg} kg"

    return {
        **proof,
        "commodity": commodity,
        "expected_kg": expected_kg,
        "reading_kg": reading,
        "ocr_matched": matched,
        "ocr_text": text,
        "verdict": verdict,
        "message": message,
        "auto_complaint": verdict == "SHORT_WEIGHT",
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Read a weighing-scale photo and check for short weight")
    ap.add_argument("image")
    ap.add_argument("--fps", required=True)
    ap.add_argument("--expected-kg", type=float, required=True)
    ap.add_argument("--commodity")
    ap.add_argument("--tolerance-kg", type=float, default=0.1)
    ap.add_argument("--lat", type=float)
    ap.add_argument("--lng", type=float)
    args = ap.parse_args()

    configure()
    print(json.dumps(check_scale(args.image, args.fps, args.expected_kg, args.commodity,
                                 args.tolerance_kg, args.lat, args.lng), indent=2, ensure_ascii=False))
