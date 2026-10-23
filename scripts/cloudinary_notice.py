"""
RationSeva - Local-language stock notice for WhatsApp (Cloudinary)
=================================================================

Builds a 1080x1080 "ration has arrived" notice for one FPS, in Telugu, Hindi
or English, purely with Cloudinary transformations (no image is rendered
locally). Stock comes from the ingest summary.json (SUMMARY_JSON, default data/summary.json); only commodities
with status AVAILABLE or LOW are listed.

Background: the shop's stock_arrival photo (darkened) if given, else a plain
base image that is uploaded once. Text uses Noto Sans Telugu / Devanagari,
uploaded once to Cloudinary as raw/authenticated font assets (OFL licence).

Usage:
    python cloudinary_notice.py --fps 0306122 --lang te
    python cloudinary_notice.py --fps 0306122 --lang hi --photo rationseva/stock_arrival/0306122/20261022_101500 --timings "9 AM - 1 PM"
"""

import argparse
import base64
import json
import math
import os
import struct
import zlib
from datetime import datetime
from functools import lru_cache

import cloudinary.api
import cloudinary.uploader
from cloudinary.exceptions import NotFound
from cloudinary.utils import cloudinary_url

from cloudinary_proof import configure

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIZE = 1080
BASE_ID = "rationseva/notice/base_1080"
BASE_RGB = (11, 61, 46)   # dark green
SCRIM_ID = "rationseva/notice/scrim_v2"   # black gradient behind text on photo backgrounds
SCRIM_ALPHA = 95                          # ~37% black where it is solid

NOTO = "https://raw.githubusercontent.com/notofonts/notofonts.github.io/main/fonts"
FONT_FILES = {
    "NotoSansTelugu-Bold.ttf": f"{NOTO}/NotoSansTelugu/hinted/ttf/NotoSansTelugu-Bold.ttf",
    "NotoSansDevanagari-Bold.ttf": f"{NOTO}/NotoSansDevanagari/hinted/ttf/NotoSansDevanagari-Bold.ttf",
    "NotoSans-Bold.ttf": f"{NOTO}/NotoSans/hinted/ttf/NotoSans-Bold.ttf",
    "NotoSans-Regular.ttf": f"{NOTO}/NotoSans/hinted/ttf/NotoSans-Regular.ttf",
}
FONT_FOLDER = "rationseva/fonts"

LANGS = {
    "te": {
        "font": "NotoSansTelugu-Bold.ttf",
        "title": "రేషన్ సరుకులు వచ్చాయి",
        "low": "స్టాక్ తక్కువ - త్వరగా రండి",
        "timings": "సమయం",
        "units": {"KG": "కిలోలు", "PKT": "ప్యాకెట్లు", "LTR": "లీటర్లు"},
        "names": {
            "Rice": "బియ్యం", "FRice": "ఫోర్టిఫైడ్ బియ్యం", "Sugar": "చక్కెర", "SUGAR HALF KG": "చక్కెర (అర కిలో)",
            "Redgram Dal": "కందిపప్పు", "Raagi": "రాగులు", "Jowar": "జొన్నలు",
            "Whole Wheat Atta": "గోధుమ పిండి", "Salt": "ఉప్పు", "Palmolein Oil": "పామాయిల్", "RagiPowder 1kg": "రాగి పిండి",
            "RG Dal One kg Pkt": "కందిపప్పు (1 కిలో ప్యాకెట్)", "WM Atta Pkt": "గోధుమ పిండి (ప్యాకెట్)",
            "Flood Dal": "వరద సహాయం - పప్పు", "Flood Poil": "వరద సహాయం - పామాయిల్",
            "Flood Rice": "వరద సహాయం - బియ్యం", "Flood Sugar HK": "వరద సహాయం - చక్కెర (అర కిలో)",
            "Flood Kit": "వరద సహాయం కిట్",
        },
    },
    "hi": {
        "font": "NotoSansDevanagari-Bold.ttf",
        "title": "राशन आ गया है",
        "low": "स्टॉक कम है - जल्दी आएं",
        "timings": "समय",
        "units": {"KG": "किलो", "PKT": "पैकेट", "LTR": "लीटर"},
        "names": {
            "Rice": "चावल", "FRice": "फोर्टिफाइड चावल", "Sugar": "चीनी", "SUGAR HALF KG": "चीनी (आधा किलो)",
            "Redgram Dal": "अरहर दाल", "Raagi": "रागी", "Jowar": "ज्वार",
            "Whole Wheat Atta": "गेहूं आटा", "Salt": "नमक", "Palmolein Oil": "पामोलीन तेल", "RagiPowder 1kg": "रागी आटा",
            "RG Dal One kg Pkt": "अरहर दाल (1 किलो पैकेट)", "WM Atta Pkt": "गेहूं आटा (पैकेट)",
            "Flood Dal": "बाढ़ राहत - दाल", "Flood Poil": "बाढ़ राहत - पामोलीन तेल",
            "Flood Rice": "बाढ़ राहत - चावल", "Flood Sugar HK": "बाढ़ राहत - चीनी (आधा किलो)",
            "Flood Kit": "बाढ़ राहत किट",
        },
    },
    "en": {
        "font": "NotoSans-Bold.ttf",
        "title": "Ration stock has arrived",
        "low": "Low stock - come soon",
        "timings": "Timings",
        "units": {"KG": "kg", "PKT": "packets", "LTR": "litres"},
        "names": {
            "FRice": "Fortified Rice", "SUGAR HALF KG": "Sugar (half kg)",
            "RG Dal One kg Pkt": "Red gram dal (1 kg pack)", "WM Atta Pkt": "Wheat atta (pack)",
            "Flood Dal": "Flood relief - Dal", "Flood Poil": "Flood relief - Palm oil",
            "Flood Rice": "Flood relief - Rice", "Flood Sugar HK": "Flood relief - Sugar (half kg)",
            "Flood Kit": "Flood relief kit",
        },
    },
}


# ---------------------------------------------------------------- one-time assets

def _png(width, height, rows, color_type):
    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    raw = zlib.compress(b"".join(b"\x00" + r * width for r in rows), 9)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, color_type, 0, 0, 0))
            + chunk(b"IDAT", raw) + chunk(b"IEND", b""))


def solid_png(width, height, rgb):
    """Minimal PNG of one colour, no Pillow needed."""
    return _png(width, height, [bytes(rgb)] * height, 2)


def scrim_png(height=256, alpha=SCRIM_ALPHA, solid=0.7):
    """1px-wide black RGBA strip: `alpha` for the top `solid` part, then fading to transparent."""
    start = int(height * solid)
    rows = [bytes((0, 0, 0, alpha if y < start else round(alpha * (height - 1 - y) / (height - 1 - start))))
            for y in range(height)]
    return _png(1, height, rows, 6)


def _exists(public_id, **kw):
    try:
        cloudinary.api.resource(public_id, **kw)
        return True
    except NotFound:
        return False


@lru_cache(maxsize=1)
def ensure_assets():
    """Upload base image + fonts if they aren't in Cloudinary yet (checked once per process)."""
    if not _exists(BASE_ID):
        data_uri = "data:image/png;base64," + base64.b64encode(solid_png(SIZE, SIZE, BASE_RGB)).decode()
        cloudinary.uploader.upload(data_uri, public_id=BASE_ID, overwrite=False, tags=["rationseva", "notice"])
    if not _exists(SCRIM_ID):
        data_uri = "data:image/png;base64," + base64.b64encode(scrim_png()).decode()
        cloudinary.uploader.upload(data_uri, public_id=SCRIM_ID, overwrite=False, tags=["rationseva", "notice"])
    for name, url in FONT_FILES.items():
        pid = f"{FONT_FOLDER}/{name}"
        # Cloudinary only uses custom fonts stored as raw + authenticated
        if not _exists(pid, resource_type="raw", type="authenticated"):
            cloudinary.uploader.upload(url, public_id=pid, resource_type="raw", type="authenticated",
                                       overwrite=False, tags=["rationseva", "font"])
    return True


# ---------------------------------------------------------------- stock data

def summary_path():
    return os.getenv("SUMMARY_JSON") or os.path.join(ROOT, "data", "summary.json")


def load_shop(fps_id):
    with open(summary_path(), encoding="utf-8") as fh:
        for shop in json.load(fh):
            if shop["fps_id"] == fps_id:
                return shop
    raise LookupError(f"FPS {fps_id} not found in the stock summary")


def fmt_qty(x, unit):
    if unit.upper() == "PKT":
        return str(math.floor(x + 1e-9))     # whole packets only; 185.35 PKT -> 185
    return f"{x:.2f}".rstrip("0").rstrip(".")


def fmt_data_time(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d %H:%M").strftime("%d %b %Y, %I:%M %p")
    except (TypeError, ValueError):
        return s or "unknown time"


# ---------------------------------------------------------------- transformation

def font_ref(name):
    return f"{FONT_FOLDER}/{name}".replace("/", ":")


def text(t, font, size, y, color="white", gravity="north_west", x=80):
    return {
        "overlay": {"font_family": font_ref(font), "font_size": size, "text": t},
        "color": color,
        "width": SIZE - 2 * x, "crop": "fit",        # wrap instead of running off the edge
        "gravity": gravity, "x": x, "y": y,
    }


def notice_lines(shop, lang):
    L = LANGS[lang]
    items = []
    for c in shop["commodities"]:
        if c["status"] not in ("AVAILABLE", "LOW"):
            continue
        name = L["names"].get(c["commodity"])
        font = L["font"]
        if name is None:
            # unmapped -> English name; the Telugu/Devanagari fonts have no Latin letters,
            # so render the whole line (incl. unit) in Noto Sans instead of showing boxes
            name, L_unit, font = LANGS["en"]["names"].get(c["commodity"], c["commodity"]), LANGS["en"], "NotoSans-Bold.ttf"
        else:
            L_unit = L
        unit = L_unit["units"].get(c["unit"].upper(), c["unit"])
        items.append({"commodity": c["commodity"], "status": c["status"], "font": font,
                      "line": f"{name}  {fmt_qty(c['closing'], c['unit'])} {unit}"})
    return items


def build_notice(fps_id, language="te", photo_public_id=None, timings=None):
    if language not in LANGS:
        raise ValueError(f"language must be one of {list(LANGS)}")
    if photo_public_id and not photo_public_id.startswith((f"rationseva/stock_arrival/{fps_id}/",
                                                           f"rationseva/incoming/stock_arrival/{fps_id}/")):
        # only this shop's stock photos - never a private doorstep/complaint original
        raise ValueError("photo_public_id must be a stock_arrival photo of this FPS")
    ensure_assets()
    if photo_public_id and not _exists(photo_public_id, type="upload", resource_type="image"):
        # otherwise we'd hand back a signed URL that 404s at Cloudinary
        raise LookupError(f"Stock photo not found: {photo_public_id}")
    shop = load_shop(fps_id)
    items = notice_lines(shop, language)
    if not items:
        raise LookupError(f"FPS {fps_id} has no AVAILABLE or LOW stock")
    L, latin = LANGS[language], "NotoSans-Regular.ttf"

    body = [text(L["title"], L["font"], 68, 90, color="rgb:FFD54F")]
    y = 250
    for it in items:
        body.append(text(it["line"], it["font"], 52, y))
        y += 80
        if it["status"] == "LOW":
            body.append(text(L["low"], L["font"], 38, y - 8, color="rgb:FF8A65"))
            y += 64
        y += 20

    layers = [{"width": SIZE, "height": SIZE, "crop": "fill", "gravity": "auto"}]
    if photo_public_id:
        # lightly darken + green tint so the stock stays visible...
        layers.append({"effect": "brightness:-35"})
        layers.append({"overlay": BASE_ID.replace("/", ":"), "opacity": 50,
                       "width": SIZE, "height": SIZE, "crop": "fill"})
        # ...and a soft black gradient only behind the text block (top) and the footer (bottom)
        scrim = {"overlay": SCRIM_ID.replace("/", ":"), "width": SIZE, "crop": "scale"}
        layers.append({**scrim, "height": min(y + 120, SIZE), "gravity": "north"})
        layers.append({**scrim, "height": 300, "gravity": "south", "angle": "vflip"})
    layers += body

    # Noto Sans Telugu/Devanagari have digits but no Latin letters ("FPS", "AM" come out as boxes),
    # so Latin text gets its own overlay in Noto Sans and only the label uses the script font.
    layers.append(text(f"FPS {fps_id}", "NotoSans-Bold.ttf", 40, 110, gravity="south_west"))
    if timings:
        t_font = "NotoSans-Bold.ttf" if timings.isascii() else L["font"]
        layers.append(text(timings, t_font, 40, 110, gravity="south_east"))
        layers.append(text(L["timings"], L["font"], 28, 166, color="rgb:DDDDDD", gravity="south_east"))
    layers.append(text(f"As per AP AePDS report, {fmt_data_time(shop.get('data_time'))}. "
                       "Not a guarantee of availability.", latin, 24, 50, color="rgb:DDDDDD", gravity="south_west"))
    layers.append({"fetch_format": "auto", "quality": "auto"})

    url, _ = cloudinary_url(photo_public_id or BASE_ID, transformation=layers, sign_url=True)
    return {
        "fps_id": fps_id,
        "language": language,
        "url": url,
        "background": "photo" if photo_public_id else "plain",
        "items": [{"commodity": i["commodity"], "status": i["status"]} for i in items],
        "data_time": shop.get("data_time"),
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Build a WhatsApp stock notice image URL for one FPS")
    ap.add_argument("--fps", required=True)
    ap.add_argument("--lang", default="te", choices=list(LANGS))
    ap.add_argument("--photo", help="public_id of a stock_arrival photo for the background")
    ap.add_argument("--timings", help='e.g. "9 AM - 1 PM"')
    args = ap.parse_args()

    configure()
    print(json.dumps(build_notice(args.fps, args.lang, args.photo, args.timings), indent=2, ensure_ascii=False))
