"""
RationSeva - API backend
========================

Thin FastAPI wrapper around scripts/cloudinary_proof.py and scripts/cloudinary_scale.py.
All Cloudinary logic lives in those scripts; this file only handles HTTP, validation
and stripping fields the frontend must never see.

Run:
    uvicorn backend.main:app --reload        (from the repo root)
"""

import io
import os
import sys
from contextlib import asynccontextmanager
from typing import Literal, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))   # cloudinary_scale imports cloudinary_proof by bare name

from cloudinary_proof import configure, upload_proof  # noqa: E402
from cloudinary_scale import check_scale              # noqa: E402

# backend/.env first, then repo-root .env; configure() then falls back to scripts/.env.
# Real environment variables (e.g. set on Render) always win - load_dotenv never overrides them.
load_dotenv(os.path.join(ROOT, "backend", ".env"))
load_dotenv(os.path.join(ROOT, ".env"))

MAX_BYTES = 10 * 1024 * 1024

# events whose original photo holds personal info (faces, card numbers) - original never leaves the server
PRIVATE_EVENTS = {"doorstep_delivery", "complaint"}

# magic bytes -> we check the actual file, not just the Content-Type the client claims
IMAGE_SIGNATURES = (
    (b"\xff\xd8\xff", "jpeg"),
    (b"\x89PNG\r\n\x1a\n", "png"),
    (b"GIF87a", "gif"),
    (b"GIF89a", "gif"),
    (b"BM", "bmp"),
    (b"II*\x00", "tiff"),
    (b"MM\x00*", "tiff"),
)


def sniff_image(head):
    for sig, kind in IMAGE_SIGNATURES:
        if head.startswith(sig):
            return kind
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "webp"
    if head[4:8] == b"ftyp" and head[8:12] in (b"heic", b"heix", b"mif1", b"msf1", b"avif"):
        return "heic"
    return None


def read_image(upload: UploadFile):
    """Return the upload as a named in-memory file; 413 if > 10 MB, 415 if not an image."""
    data = upload.file.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise HTTPException(413, "Image larger than 10 MB")
    if not data:
        raise HTTPException(400, "Empty file")
    if not (upload.content_type or "").startswith("image/") or sniff_image(data[:16]) is None:
        raise HTTPException(415, "File must be an image (jpeg, png, webp, heic, gif, bmp, tiff)")
    buf = io.BytesIO(data)
    buf.name = upload.filename or "upload"
    return buf


def cloudinary_call(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except HTTPException:
        raise
    except Exception as e:  # cloudinary.exceptions.Error, network errors, ...
        raise HTTPException(502, f"Cloudinary upload failed: {type(e).__name__}") from e


@asynccontextmanager
async def lifespan(app):
    configure()   # fails fast if Cloudinary creds are missing
    yield


app = FastAPI(title="RationSeva API", lifespan=lifespan)

origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
origins += [o.strip() for o in os.getenv("FRONTEND_ORIGIN", "").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/proof")
def proof(
    image: UploadFile = File(...),
    fps_id: str = Form(...),
    event: Literal["stock_arrival", "doorstep_delivery", "weighing", "complaint"] = Form(...),
    lat: Optional[float] = Form(None),
    lng: Optional[float] = Form(None),
    note: Optional[str] = Form(None),
):
    result = cloudinary_call(upload_proof, read_image(image), fps_id, event, lat, lng, note)
    result.pop("_raw", None)
    if event in PRIVATE_EVENTS:
        result.pop("original_url", None)
    return result


@app.post("/scale-check")
def scale_check(
    image: UploadFile = File(...),
    fps_id: str = Form(...),
    expected_kg: float = Form(..., gt=0),
    commodity: Optional[str] = Form(None),
    tolerance_kg: float = Form(0.1, ge=0),
    lat: Optional[float] = Form(None),
    lng: Optional[float] = Form(None),
):
    result = cloudinary_call(check_scale, read_image(image), fps_id, expected_kg, commodity, tolerance_kg, lat, lng)
    result.pop("_raw", None)
    return result
