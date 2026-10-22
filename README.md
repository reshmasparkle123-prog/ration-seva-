# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).



## Backend API (FastAPI)

`backend/main.py` exposes the Cloudinary scripts in `scripts/` over HTTP for the React app.

| Endpoint | Body (multipart/form-data) | Returns |
|---|---|---|
| `GET /health` | - | `{"status": "ok"}` |
| `POST /proof` | `image`, `fps_id`, `event` (`stock_arrival` \| `doorstep_delivery` \| `weighing` \| `complaint`), optional `lat`, `lng`, `note` | stamped / thumbnail URLs. For `doorstep_delivery` and `complaint`, `original_url` (unblurred) is **not** returned |
| `POST /scale-check` | `image`, `fps_id`, `expected_kg`, optional `commodity`, `tolerance_kg` (default 0.1), `lat`, `lng` | OCR reading + `verdict` (`OK` \| `SHORT_WEIGHT` \| `NEEDS_REVIEW` \| `UNREADABLE` \| `OCR_UNAVAILABLE`) |
| `POST /notice` | `fps_id`, optional `language` (`te` default \| `hi` \| `en`), `photo_public_id` (a `stock_arrival` photo of that FPS, used as darkened background), `timings` (e.g. `9 AM - 1 PM`) | signed 1080x1080 WhatsApp notice `url` listing AVAILABLE / LOW stock from `summary.json` |

Uploads must be real images (checked by file signature) and at most 10 MB. Otherwise the API returns 415 or 413.

### Run locally

```bash
python -m pip install -r backend/requirements.txt
cp backend/.env.example backend/.env    # fill in Cloudinary creds (scripts/.env is also picked up)
uvicorn backend.main:app --reload       # run from the repo root -> http://localhost:8000/docs
```

CORS allows `http://localhost:5173` (Vite) by default. Add more origins with `FRONTEND_ORIGIN` (comma-separated).

`/notice` reads stock from the ingest output (`python scripts/rationseva_ingest.py data`), path set by `SUMMARY_JSON` (default `data/summary.json`, a committed snapshot of all 480 Alluri Sitharama Raju shops, data time 2026-10-20 22:00). The first call uploads the Noto fonts and plain background to Cloudinary once.

### Deploy to Render

1. New → **Web Service** → connect this repo. Leave **Root Directory** empty, because the backend imports `scripts/`.
2. Runtime: **Python 3**
   - Build command: `pip install -r backend/requirements.txt`
   - Start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
   - Health check path: `/health`
3. Environment variables: `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`, and `FRONTEND_ORIGIN` (your deployed frontend URL, e.g. `https://rationseva.vercel.app`). `/notice` uses the committed `data/summary.json` snapshot unless `SUMMARY_JSON` points elsewhere.

`.env` files are git-ignored. Never commit Cloudinary creds.
