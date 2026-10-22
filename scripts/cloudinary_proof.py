"""
RationSeva - Cloudinary photo proof
===================================

Uploads a proof photo (stock arrival / doorstep delivery / weighing scale)
to Cloudinary and returns:
  - original_url : the untouched original (kept as evidence)
  - stamped_url  : same photo with a burned-in stamp
                   "FPS 0306122 | STOCK ARRIVED | 21 Oct 2026 07:05 PM IST"
                   + GPS line, optimised for slow rural networks (f_auto, q_auto)
  - thumb_url    : small preview for lists

The timestamp is taken on the SERVER, not from the phone, so it can't be faked
by changing the phone's clock. Metadata (fps_id, event, time, GPS) is also stored
on the asset in Cloudinary as context + tags, so photos are searchable later.

Setup:
    python -m pip install cloudinary python-dotenv
    .env in the same folder:
        CLOUDINARY_CLOUD_NAME=...
        CLOUDINARY_API_KEY=...
        CLOUDINARY_API_SECRET=...

Usage:
    python cloudinary_proof.py photo.jpg --fps 0306122 --event stock_arrival
    python cloudinary_proof.py photo.jpg --fps 0306122 --event doorstep_delivery --lat 15.8281 --lng 78.0373
"""

import argparse
import json
import os
import re
import time
from datetime import datetime, timedelta, timezone

import cloudinary
import cloudinary.api
import cloudinary.exceptions
import cloudinary.uploader
from cloudinary.utils import api_sign_request, cloudinary_url
from dotenv import load_dotenv

IST = timezone(timedelta(hours=5, minutes=30))

EVENTS = {
    "stock_arrival": "STOCK ARRIVED",
    "doorstep_delivery": "DELIVERED AT DOORSTEP",
    "weighing": "WEIGHING PROOF",
    "complaint": "COMPLAINT EVIDENCE",
}


def configure():
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
    missing = [k for k in ("CLOUDINARY_CLOUD_NAME", "CLOUDINARY_API_KEY", "CLOUDINARY_API_SECRET") if not os.getenv(k)]
    if missing:
        raise SystemExit(f"Missing in .env: {', '.join(missing)}")
    cloudinary.config(
        cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
        api_key=os.getenv("CLOUDINARY_API_KEY"),
        api_secret=os.getenv("CLOUDINARY_API_SECRET"),
        secure=True,
    )


def text_layer(text, size, y, bold=True):
    """One line of white text on a dark translucent strip, bottom-left."""
    return {
        "overlay": {
            "font_family": "Arial",
            "font_size": size,
            "font_weight": "bold" if bold else "normal",
            "text": text,
        },
        "color": "white",
        "background": "rgb:000000B3",   # black at ~70% opacity
        "gravity": "south_west",
        "x": 20,
        "y": y,
    }


# which privacy blur each event gets by default
DEFAULT_BLUR = {
    "stock_arrival": "none",           # photo of sacks, no people
    "weighing": "none",                # we NEED the scale digits readable
    "doorstep_delivery": "faces",      # beneficiary's face at their home
    "complaint": "faces+text",         # may show faces, ration card / Aadhaar numbers
}


def privacy_layers(blur):
    """Cloudinary effects that hide personal info BEFORE the stamp is drawn."""
    layers = []
    if blur in ("faces", "faces+text"):
        layers.append({"effect": "pixelate_faces:20"})                        # built-in face detection
    if blur in ("text", "faces+text"):
        layers.append({"effect": "pixelate_region:20", "gravity": "ocr_text"})  # needs OCR add-on
    return layers


def stamp_transformation(fps_id, event, captured_at, lat=None, lng=None, blur="none"):
    line1 = f"FPS {fps_id} | {EVENTS[event]}"
    line2 = captured_at.strftime("%d %b %Y %I:%M %p IST")
    if lat is not None and lng is not None:
        line2 += f" | GPS {lat:.5f}, {lng:.5f}"
    return [
        {"width": 1280, "crop": "limit"},          # cap size for phones
        *privacy_layers(blur),                     # blur faces / text first...
        text_layer(line2, 26, 20, bold=False),     # ...then draw the stamp on top (stays readable)
        text_layer(line1, 34, 62),
        {"fetch_format": "auto", "quality": "auto"},  # smallest format the device supports
    ]


def upload_proof(image, fps_id, event, lat=None, lng=None, note=None, blur="auto", **upload_extra):
    if event not in EVENTS:
        raise ValueError(f"event must be one of {list(EVENTS)}")
    if blur == "auto":
        blur = DEFAULT_BLUR[event]
    captured_at = datetime.now(IST)

    # Photos that need blurring hold personal info -> store them PRIVATE ("authenticated"):
    # the unblurred original can't be opened by guessing the URL, only via signed links.
    delivery = "authenticated" if blur != "none" else "upload"

    res = cloudinary.uploader.upload(
        image,
        folder=f"rationseva/{event}/{fps_id}",
        public_id=captured_at.strftime("%Y%m%d_%H%M%S"),
        tags=["rationseva", event, f"fps_{fps_id}"],
        context=proof_context(fps_id, event, captured_at, lat, lng, note),
        resource_type="image",
        type=delivery,
        **upload_extra,
    )
    return proof_result(res, fps_id, event, captured_at, lat, lng, blur, delivery)


def proof_context(fps_id, event, captured_at, lat=None, lng=None, note=None):
    context = {"fps_id": fps_id, "event": event, "captured_at": captured_at.isoformat()}
    if lat is not None and lng is not None:
        context.update({"lat": str(lat), "lng": str(lng)})
    if note:
        context["note"] = note
    return context


def proof_result(res, fps_id, event, captured_at, lat, lng, blur, delivery):
    """Stamped / thumb / original URLs for an asset already in Cloudinary (res = upload or Admin API response)."""
    pid = res["public_id"]
    # sign_url=True: required for add-on effects (OCR text blur), and stops anyone
    # from editing the URL to strip the blur or the stamp.
    signed = {"type": delivery, "sign_url": True}
    original_url, _ = cloudinary_url(pid, format=res.get("format"), **signed)
    stamped_url, _ = cloudinary_url(pid, transformation=stamp_transformation(fps_id, event, captured_at, lat, lng, blur), **signed)
    thumb_url, _ = cloudinary_url(pid, transformation=[
        *privacy_layers(blur),
        {"width": 300, "height": 300, "crop": "fill", "gravity": "auto"},
        {"fetch_format": "auto", "quality": "auto"},
    ], **signed)

    return {
        "fps_id": fps_id,
        "event": event,
        "captured_at": captured_at.isoformat(),
        "lat": lat,
        "lng": lng,
        "public_id": pid,
        "original_url": original_url,   # unblurred - store for officials only, never show publicly
        "storage": delivery,
        "stamped_url": stamped_url,
        "thumb_url": thumb_url,
        "privacy_blur": blur,
        "bytes": res.get("bytes"),
        "_raw": res,   # full Cloudinary response (used by the scale reader); dropped when printing
    }


# ---------------------------------------------------------------------------
# Signed Upload Widget: the browser uploads straight to Cloudinary into
# rationseva/incoming/<event>/<fps_id>, then hands us the public_id.
# ---------------------------------------------------------------------------

INCOMING_ROOT = "rationseva/incoming"
FPS_RE = re.compile(r"[0-9A-Za-z]{1,20}")
COORDS_RE = re.compile(r"\d{1,5},\d{1,5},\d{1,5},\d{1,5}")
SIGNATURE_MAX_SKEW = 600   # seconds; Cloudinary itself rejects signatures older than 1 hour


def incoming_folder(event, fps_id):
    if event not in EVENTS:
        raise ValueError(f"event must be one of {list(EVENTS)}")
    if not FPS_RE.fullmatch(fps_id or ""):
        raise ValueError("fps_id must be 1-20 letters/digits")
    return f"{INCOMING_ROOT}/{event}/{fps_id}"


def default_delivery(event):
    """Same rule as upload_proof with blur='auto': anything that gets blurred is stored private."""
    return "authenticated" if DEFAULT_BLUR[event] != "none" else "upload"


def sign_upload(event, fps_id, timestamp=None, custom_coordinates=None):
    """
    Signature for a widget upload. Only server-chosen params are signed, so a client that
    changes folder / type / tags / ocr gets its upload rejected by Cloudinary.
    timestamp / custom_coordinates only let us re-sign what the widget itself adds (see README).
    """
    now = int(time.time())
    if timestamp is None:
        timestamp = now
    elif abs(int(timestamp) - now) > SIGNATURE_MAX_SKEW:
        raise ValueError("timestamp too far from server time")
    params = {
        "timestamp": int(timestamp),
        "folder": incoming_folder(event, fps_id),
        "type": default_delivery(event),
        "tags": f"rationseva,incoming,{event},fps_{fps_id}",
        "source": "uw",   # the Upload Widget always adds and signs this
    }
    if event == "weighing":
        params["ocr"] = "adv_ocr"
    if os.getenv("CLOUDINARY_UPLOAD_PRESET"):
        params["upload_preset"] = os.getenv("CLOUDINARY_UPLOAD_PRESET")
    if custom_coordinates:
        if not COORDS_RE.fullmatch(custom_coordinates):
            raise ValueError("custom_coordinates must be x,y,w,h")
        params["custom_coordinates"] = custom_coordinates
    cfg = cloudinary.config()
    return {
        **params,
        "tags": params["tags"].split(","),
        "signature": api_sign_request(params, cfg.api_secret),
        "api_key": cfg.api_key,
        "cloud_name": cfg.cloud_name,
    }


def proof_from_incoming(public_id, fps_id, event, lat=None, lng=None, note=None):
    """
    Same result as upload_proof, for a photo the widget already uploaded.
    captured_at = our server time now (not the phone's); uploaded_at = Cloudinary's created_at.
    """
    folder = incoming_folder(event, fps_id)
    # exactly one segment after our folder: rejects other shops / events, private originals, '..'
    if not re.fullmatch(re.escape(folder) + r"/[A-Za-z0-9_-]{1,100}", public_id or ""):
        raise ValueError(f"public_id must be a widget upload under {folder}/")
    delivery = default_delivery(event)
    captured_at = datetime.now(IST)
    extra = {}
    try:
        res = cloudinary.api.resource(public_id, type=delivery, resource_type="image")
        if event == "weighing" and (res.get("info") or {}).get("ocr", {}).get("adv_ocr", {}).get("status") != "complete":
            extra["ocr"] = "adv_ocr"   # no OCR result stored with the asset -> run it now
        upd = cloudinary.api.update(public_id, type=delivery, resource_type="image",
                                    context=proof_context(fps_id, event, captured_at, lat, lng, note), **extra)
    except cloudinary.exceptions.NotFound as e:
        raise LookupError("Uploaded photo not found") from e
    if upd.get("info"):
        res = {**res, "info": upd["info"]}
    result = proof_result(res, fps_id, event, captured_at, lat, lng, DEFAULT_BLUR[event], delivery)
    result["uploaded_at"] = res.get("created_at")
    return result


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Upload a RationSeva proof photo to Cloudinary")
    ap.add_argument("image", help="local file path or image URL")
    ap.add_argument("--fps", required=True, help="FPS id, e.g. 0306122")
    ap.add_argument("--event", default="stock_arrival", choices=list(EVENTS))
    ap.add_argument("--lat", type=float)
    ap.add_argument("--lng", type=float)
    ap.add_argument("--note")
    ap.add_argument("--blur", default="auto", choices=["auto", "none", "faces", "text", "faces+text"],
                    help="privacy blur; 'auto' picks per event ('text' needs the OCR add-on)")
    args = ap.parse_args()

    configure()
    result = upload_proof(args.image, args.fps, args.event, args.lat, args.lng, args.note, args.blur)
    result.pop("_raw")
    print(json.dumps(result, indent=2))
    print("\nOpen stamped_url in your browser to see the stamp.")