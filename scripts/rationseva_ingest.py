"""
RationSeva - AP AePDS stock ingest + consistency checks
=======================================================

Reads the Excel exports from the AP AePDS "Date wise Stock Details" report
(one zip / folder per FPS, files named
    {district}_{afso}_{fpsid}_Main.xlsx
    {district}_{afso}_{fpsid}_{commodity}_Scheme.xlsx )
and produces clean, Supabase-ready CSV/JSON plus stock-status flags.

Usage:
    pip install openpyxl
    python rationseva_ingest.py data/Alluri_Sitharama_Raju.zip  [more zips or folders...]
    python rationseva_ingest.py data/ --out output/ --stale-hours 48

Outputs (in --out, default ./output):
    stock.csv         one row per FPS x commodity  (from *_Main.xlsx)
    scheme_stock.csv  one row per FPS x commodity x scheme (from *_Scheme.xlsx)
    flags.csv         every issue found by the checks
    summary.json      per-FPS summary the frontend can show directly
"""

import argparse
import csv
import io
import json
import os
import re
import sys
import zipfile
from datetime import datetime

import openpyxl

# ---------------------------------------------------------------- config ---
TOLERANCE = 0.01          # allowed rounding difference in kg/pkt
LOW_STOCK_RATIO = 0.10    # closing < 10% of month's available stock => LOW
DEFAULT_STALE_HOURS = 48  # data older than this => STALE
# empty sacks the shop returns (10KG BAG, Feb 15Kg Bag, Empty Gunny Bag ...) - not ration for beneficiaries
PACKAGING_RE = re.compile(r"\bbags?\b|gunny", re.I)

MAIN_RE = re.compile(r"^(?P<district>.+)_(?P<afso>[^_]+)_(?P<fps>\d{5,})_Main\.xlsx$", re.I)
SCHEME_RE = re.compile(r"^(?P<district>.+)_(?P<afso>[^_]+)_(?P<fps>\d{5,})_(?P<commodity>.+)_Scheme\.xlsx$", re.I)

# header keyword -> our column name (checked in order)
HEADER_MAP = [
    ("sl.no", "sl_no"),
    ("commodity", "commodity"),
    ("scheme", "scheme"),
    ("units", "unit"),
    ("ob qty", "opening"),
    ("received", "received"),
    ("extra", "extra"),
    ("moved", "moved"),
    ("issued", "issued"),
    ("cb qty", "closing"),
]
NUM_COLS = ["opening", "received", "extra", "moved", "issued", "closing"]

MONTHS = "January February March April May June July August September October November December".split()


# ------------------------------------------------------------- helpers ---
def to_num(v):
    if v is None or v == "":
        return 0.0
    try:
        return float(str(v).replace(",", "").strip())
    except ValueError:
        return None


def map_header(cell):
    """Turn a (possibly long, prefixed) header cell into our column name."""
    if cell is None:
        return None
    text = str(cell).lower()
    # Main.xlsx glues the report title in front of every header - keep the tail
    if "2026" in text or "date wise" in text:
        text = re.split(r"\d{2}-\d{2}-\d{4}", text)[-1]
    for key, name in HEADER_MAP:
        if key in text:
            return name
    return None


def parse_meta(text):
    """Pull report month + 'as on' date from a title/header string."""
    meta = {}
    m = re.search(r"(" + "|".join(MONTHS) + r")'?\s*(\d{4})", text or "")
    if m:
        meta["report_month"] = f"{m.group(2)}-{MONTHS.index(m.group(1)) + 1:02d}"
    d = re.search(r"on\s+(\d{2})-(\d{2})-(\d{4})", text or "")
    if d:
        meta["report_date"] = f"{d.group(3)}-{d.group(2)}-{d.group(1)}"
    return meta


def parse_data_time(text):
    m = re.search(r"Data Time:\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})", str(text or ""))
    return m.group(1) if m else None


def read_sheet(blob):
    wb = openpyxl.load_workbook(io.BytesIO(blob), read_only=True, data_only=True)
    ws = wb.worksheets[0]
    rows = [list(r) for r in ws.iter_rows(values_only=True)]
    wb.close()
    return rows


def parse_table(rows, label_col):
    """Generic parser for both Main and Scheme sheets."""
    meta, data_time, header_idx, cols = {}, None, None, {}

    for i, row in enumerate(rows):
        first = next((c for c in row if c not in (None, "")), None)
        if first is None:
            continue
        if data_time is None and "Data Time" in str(first):
            data_time = parse_data_time(first)
            continue
        if not meta:
            meta = parse_meta(" ".join(str(c) for c in row if c))
        if header_idx is None:
            mapped = {j: map_header(c) for j, c in enumerate(row)}
            names = set(mapped.values())
            if label_col in names and "closing" in names:
                header_idx = i
                cols = {name: j for j, name in mapped.items() if name}
    if header_idx is None:
        for row in rows:
            names = {map_header(c) for c in row}
            if label_col == "scheme" and "commodity" in names and "closing" in names:
                raise ValueError("WRONG REPORT: file has the commodity-wise table, not the scheme "
                                 "breakdown - re-download this file")
        raise ValueError("could not find header row")

    records = []
    for row in rows[header_idx + 1:]:
        label = row[cols[label_col]] if cols[label_col] < len(row) else None
        sl = row[cols["sl_no"]] if "sl_no" in cols and cols["sl_no"] < len(row) else None
        if label in (None, "") or to_num(sl) is None:   # footer rows: Data Time / Export to Excel
            continue
        rec = {label_col: str(label).strip(), "unit": str(row[cols["unit"]]).strip() if "unit" in cols else ""}
        for c in NUM_COLS:
            rec[c] = to_num(row[cols[c]]) if c in cols else 0.0
        records.append(rec)
    return meta, data_time, records


# ---------------------------------------------------------------- checks ---
def check_row(r, data_age_hours, stale_hours):
    """Return (status, [flags]) for one FPS x commodity row."""
    flags = []
    available = r["opening"] + r["received"] + r["extra"] + r["moved"]
    expected_cb = available - r["issued"]

    if any(r[c] is None for c in NUM_COLS):
        return "UNKNOWN", [("BAD_NUMBER", "error", "Non-numeric value in report")]

    if abs(expected_cb - r["closing"]) > TOLERANCE:
        flags.append(("BALANCE_MISMATCH", "error",
                      f"OB+Recv+Extra+Moved-Issued = {expected_cb:.2f} but report says CB = {r['closing']:.2f}"))
    if any(r[c] < 0 for c in NUM_COLS if c != "moved"):
        flags.append(("NEGATIVE_VALUE", "error", "Negative quantity in report"))
    if r["unit"].upper() == "PKT" and abs(r["closing"] - round(r["closing"])) > TOLERANCE:
        flags.append(("FRACTIONAL_PACKETS", "warning",
                      f"Closing balance {r['closing']} is not a whole number of packets"))
    if r["received"] > 0 and r["issued"] == 0:
        flags.append(("RECEIVED_NOT_ISSUED", "warning",
                      "Stock received this month but nothing issued yet - distribution may not have started"))
    if data_age_hours is not None and data_age_hours > stale_hours:
        flags.append(("STALE_DATA", "warning", f"Report data is {data_age_hours:.0f}h old"))

    if PACKAGING_RE.search(r["commodity"]):
        status = "PACKAGING"      # kept in stock.csv, never shown as stock or flagged LOW/OUT
    elif available == 0 and r["issued"] == 0:
        status = "NOT_ALLOTTED"
    elif r["closing"] <= TOLERANCE:
        status = "OUT_OF_STOCK"
    elif available > 0 and r["closing"] / available < LOW_STOCK_RATIO:
        status = "LOW"
        flags.append(("LOW_STOCK", "info",
                      f"Only {r['closing']:.2f} {r['unit']} left ({r['closing'] / available:.1%} of this month's stock)"))
    else:
        status = "AVAILABLE"
    return status, flags


# ------------------------------------------------------------ discovery ---
def iter_files(paths):
    """Yield (filename, bytes) for every xlsx in the given zips/folders, skipping macOS junk."""
    for p in paths:
        if os.path.isdir(p):
            for root, _, files in os.walk(p):
                if "__MACOSX" in root:
                    continue
                for f in files:
                    if f.lower().endswith(".xlsx") and not f.startswith("._"):
                        with open(os.path.join(root, f), "rb") as fh:
                            yield f, fh.read()
                    elif f.lower().endswith(".zip"):
                        yield from iter_files([os.path.join(root, f)])
        elif p.lower().endswith(".zip"):
            with zipfile.ZipFile(p) as z:
                for info in z.infolist():
                    name = os.path.basename(info.filename)
                    if "__MACOSX" in info.filename or name.startswith("._") or not name.lower().endswith(".xlsx"):
                        continue
                    yield name, z.read(info)
        elif p.lower().endswith(".xlsx"):
            with open(p, "rb") as fh:
                yield os.path.basename(p), fh.read()


# ------------------------------------------------------------------ main ---
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", nargs="+", help="zip files, folders or xlsx files")
    ap.add_argument("--out", default="output")
    ap.add_argument("--stale-hours", type=float, default=DEFAULT_STALE_HOURS)
    ap.add_argument("--now", help="override current time for demos, e.g. '2026-10-21 18:00'")
    args = ap.parse_args()

    now = datetime.strptime(args.now, "%Y-%m-%d %H:%M") if args.now else datetime.now()
    os.makedirs(args.out, exist_ok=True)

    stock, scheme_stock, flags, skipped = [], [], [], []
    fps_info = {}

    for name, blob in iter_files(args.inputs):
        m_main, m_sch = MAIN_RE.match(name), SCHEME_RE.match(name)
        try:
            if m_main:
                g = m_main.groupdict()
                meta, data_time, recs = parse_table(read_sheet(blob), "commodity")
                fps_info[g["fps"]] = {"fps_id": g["fps"], "district": g["district"], "afso": g["afso"],
                                      "data_time": data_time, **meta}
                for r in recs:
                    stock.append({"fps_id": g["fps"], "district": g["district"], "afso": g["afso"],
                                  **meta, "data_time": data_time, **r, "source_file": name})
            elif m_sch:
                g = m_sch.groupdict()
                meta, data_time, recs = parse_table(read_sheet(blob), "scheme")
                for r in recs:
                    scheme_stock.append({"fps_id": g["fps"], "district": g["district"], "afso": g["afso"],
                                         "commodity": g["commodity"], **meta, "data_time": data_time,
                                         **r, "source_file": name})
            else:
                skipped.append((name, "filename does not match expected pattern"))
        except Exception as e:  # keep going on one bad file
            skipped.append((name, str(e)))

    # ---- checks on Main rows
    for r in stock:
        age = None
        if r.get("data_time"):
            age = (now - datetime.strptime(r["data_time"], "%Y-%m-%d %H:%M")).total_seconds() / 3600
        status, fl = check_row(r, age, args.stale_hours)
        r["status"] = status
        r["data_age_hours"] = round(age, 1) if age is not None else None
        for code, sev, msg in fl:
            flags.append({"fps_id": r["fps_id"], "commodity": r["commodity"], "flag": code,
                          "severity": sev, "message": msg, "data_time": r["data_time"]})

    # ---- cross-check: scheme rows must add up to the Main row
    totals = {}
    for s in scheme_stock:
        k = (s["fps_id"], s["commodity"])
        t = totals.setdefault(k, {c: 0.0 for c in NUM_COLS})
        for c in NUM_COLS:
            t[c] += s[c] or 0
    main_idx = {(r["fps_id"], r["commodity"]): r for r in stock}
    for k, t in totals.items():
        r = main_idx.get(k)
        if r is None:
            flags.append({"fps_id": k[0], "commodity": k[1], "flag": "SCHEME_WITHOUT_MAIN", "severity": "warning",
                          "message": "Scheme file exists but commodity missing from Main report", "data_time": None})
            continue
        diffs = [c for c in NUM_COLS if abs(t[c] - r[c]) > TOLERANCE]
        if diffs:
            flags.append({"fps_id": k[0], "commodity": k[1], "flag": "SCHEME_TOTAL_MISMATCH", "severity": "error",
                          "message": "Scheme-wise totals differ from Main report in: " + ", ".join(diffs),
                          "data_time": r["data_time"]})

    # ---- write outputs
    def write_csv(path, rows):
        if not rows:
            return
        keys = list(dict.fromkeys(k for r in rows for k in r))
        with open(path, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=keys)
            w.writeheader()
            w.writerows(rows)

    write_csv(os.path.join(args.out, "stock.csv"), stock)
    write_csv(os.path.join(args.out, "scheme_stock.csv"), scheme_stock)
    write_csv(os.path.join(args.out, "flags.csv"), flags)

    summary = []
    for fps, info in fps_info.items():
        rows = [r for r in stock if r["fps_id"] == fps]
        summary.append({
            **info,
            "source": "AP AePDS - Date wise Stock Details (public report)",
            "is_live": False,
            "commodities": [
                {"commodity": r["commodity"], "unit": r["unit"], "closing": r["closing"],
                 "received": r["received"], "issued": r["issued"], "status": r["status"]}
                for r in rows if r["status"] not in ("NOT_ALLOTTED", "PACKAGING")
            ],
            "not_allotted_count": sum(r["status"] == "NOT_ALLOTTED" for r in rows),
            "flags": [f for f in flags if f["fps_id"] == fps],
        })
    with open(os.path.join(args.out, "summary.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, ensure_ascii=False)

    # ---- console report
    print(f"Shops: {len(fps_info)} | stock rows: {len(stock)} | scheme rows: {len(scheme_stock)} | flags: {len(flags)}")
    for s in summary:
        print(f"\nFPS {s['fps_id']} ({s['afso']}, {s['district']}) - data time {s['data_time']}")
        for c in s["commodities"]:
            print(f"  {c['commodity']:<22} {c['closing']:>10.2f} {c['unit']:<4} {c['status']}")
        print(f"  ({s['not_allotted_count']} commodities not allotted this month)")
        for f in s["flags"]:
            print(f"  [{f['severity'].upper()}] {f['commodity']}: {f['flag']} - {f['message']}")
    for name, why in skipped:
        print(f"SKIPPED {name}: {why}", file=sys.stderr)
    print(f"\nWrote outputs to {os.path.abspath(args.out)}")


if __name__ == "__main__":
    main()