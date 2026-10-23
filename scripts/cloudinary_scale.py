"""
RationSeva - Weighing-scale photo reader (Cloudinary OCR)
=========================================================

Beneficiaries photograph a weighing-scale display while collecting ration.
Cloudinary OCR extracts text, and the result is compared with the expected
weight. Ambiguous readings are sent for review rather than treated as
confirmed shortages.

Needs: Cloudinary OCR add-on.
"""

import argparse
import json
import re

from cloudinary_proof import configure, upload_proof

NUM_RE = re.compile(
    r"(\d{1,3}(?:[.,]\d{1,3})?)\s*(kg|kgs|g|gm|gms)?\b",
    re.I,
)


def ocr_text(cloudinary_response):
    """Return OCR text and status."""
    ocr = (
        (cloudinary_response.get("info") or {})
        .get("ocr", {})
        .get("adv_ocr", {})
    )

    if ocr.get("status") != "complete":
        return None, ocr.get("status", "not_requested")

    try:
        return ocr["data"][0]["textAnnotations"][0]["description"], "complete"
    except (KeyError, IndexError, TypeError):
        return "", "complete"


def pick_weight_kg(text):
    """
    Conservatively identify a possible scale reading.

    Rejects lines that look like product descriptions or specifications.
    Returns (weight_in_kg, matched_text) only when exactly one plausible
    candidate remains. This is a heuristic, not proof that the image shows
    a genuine live scale reading.
    """
    if not text:
        return None, None

    candidates = []

    ignored_terms = re.compile(
        r"\b(max|min|capacity|cap|model|serial|mercadolibre|amazon|"
        r"price|product|kitchen scale|unit|resolution|division)\b",
        re.I,
    )

    for line in text.splitlines():
        line = line.strip()

        if not line or ignored_terms.search(line):
            continue

        matches = list(NUM_RE.finditer(line))

        # Do not guess when a line contains multiple numbers.
        if len(matches) != 1:
            continue

        match = matches[0]
        raw = match.group(1)
        unit = (match.group(2) or "").lower()

        # A decimal or explicit weight unit is required.
        if "." not in raw and "," not in raw and not unit:
            continue

        try:
            value = float(raw.replace(",", "."))
        except ValueError:
            continue

        if unit in ("g", "gm", "gms"):
            value /= 1000.0

        # Plausibility filter for ration weights.
        if not 0 < value <= 100:
            continue

        candidates.append((round(value, 3), match.group(0).strip()))

    # Ambiguous OCR results must not be treated as reliable measurements.
    if len(candidates) != 1:
        return None, None

    return candidates[0]


def check_scale(
    image,
    fps_id,
    expected_kg,
    commodity=None,
    tolerance_kg=0.1,
    lat=None,
    lng=None,
):
    """Upload weighing evidence and compare a possible reading with entitlement."""
    proof = upload_proof(
        image,
        fps_id,
        "weighing",
        lat,
        lng,
        note=f"{commodity or 'ration'} expected {expected_kg} kg",
        ocr="adv_ocr",
    )

    raw = proof.pop("_raw", {})
    text, status = ocr_text(raw)
    reading, matched = pick_weight_kg(text)

    if status != "complete":
        verdict = "OCR_UNAVAILABLE"
        message = (
            f"OCR status: {status}. Check whether the Cloudinary OCR "
            "add-on is enabled."
        )

    elif reading is None:
        verdict = "UNREADABLE"
        message = (
            "Couldn't identify one unambiguous weight reading. "
            "Retake a clear photo of the scale display or enter the "
            "reading manually for review."
        )

    elif reading > expected_kg * 1.5 and reading > expected_kg + 2:
        verdict = "NEEDS_REVIEW"
        message = (
            f"Possible reading {reading} kg is far above the expected "
            f"{expected_kg} kg. Check the photo and reading manually."
        )

    elif reading + tolerance_kg < expected_kg:
        short = expected_kg - reading
        verdict = "SHORT_WEIGHT"
        message = (
            f"Possible reading {reading} kg is below the expected "
            f"{expected_kg} kg by {short:.2f} kg. Human review is required."
        )

    else:
        verdict = "OK"
        message = (
            f"Possible reading {reading} kg is within the configured "
            f"tolerance of the expected {expected_kg} kg. "
            "Verify the photo before relying on this result."
        )

    return {
        **proof,
        "commodity": commodity,
        "expected_kg": expected_kg,
        "reading_kg": reading,
        "ocr_matched": matched,
        "ocr_text": text,
        "verdict": verdict,
        "message": message,
        "auto_complaint": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Read a weighing-scale photo and flag possible discrepancies"
    )
    parser.add_argument("image")
    parser.add_argument("--fps", required=True)
    parser.add_argument("--expected-kg", type=float, required=True)
    parser.add_argument("--commodity")
    parser.add_argument("--tolerance-kg", type=float, default=0.1)
    parser.add_argument("--lat", type=float)
    parser.add_argument("--lng", type=float)

    args = parser.parse_args()

    configure()

    result = check_scale(
        args.image,
        args.fps,
        args.expected_kg,
        args.commodity,
        args.tolerance_kg,
        args.lat,
        args.lng,
    )

    print(json.dumps(result, indent=2, ensure_ascii=False))