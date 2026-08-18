"""Generate QR codes for the presentation tool's scene/question pages.

Payload format matches design/LLD.md §2: "<page_type>:<id>", e.g.
"scene:story_03_scene_2" or "question:story_03_scene_2_q". One PNG per row.

Usage:
    python generate_qr.py pages.csv --out-dir qr_codes

pages.csv columns: page_type,id
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import qrcode


def generate(payload: str, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{payload.replace(':', '_')}.png"
    qrcode.make(payload).save(path)
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pages_csv", help="CSV with columns: page_type,id")
    parser.add_argument("--out-dir", default="./qr_codes")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    count = 0
    with open(args.pages_csv, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            payload = f"{row['page_type']}:{row['id']}"
            path = generate(payload, out_dir)
            print(f"{payload} -> {path}")
            count += 1

    if count == 0:
        raise SystemExit(f"No rows found in {args.pages_csv}")
    print(f"Generated {count} QR codes in {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
