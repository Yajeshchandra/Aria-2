from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def count_jsonl(path: Path) -> int:
    count = 0
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.strip():
                count += 1
    return count


def human_bytes(size: int) -> str:
    value = float(size)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024.0 or unit == "TB":
            return f"{value:.1f} {unit}"
        value /= 1024.0
    return f"{size} B"


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect a Watch and Tell sensor session")
    parser.add_argument("session", nargs="?", help="Optional sensor-session directory")
    parser.add_argument(
        "--no-fallback-count",
        action="store_true",
        help="Do not count JSONL lines when manifest counts are missing",
    )
    args = parser.parse_args()

    if args.session:
        session = Path(args.session).expanduser().resolve()
    else:
        root = Path("data/sensors")
        sessions = sorted(path for path in root.glob("*") if path.is_dir())
        if not sessions:
            raise SystemExit("No sensor sessions found under data/sensors")
        session = sessions[-1]

    if not session.is_dir():
        raise SystemExit(f"Session directory does not exist: {session}")

    print("Session:", session)
    manifest_path = session / "manifest.json"
    manifest: dict[str, Any] = {}
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        print("Created UTC:", manifest.get("created_utc"))
        print("Ended UTC:", manifest.get("ended_utc"))
        print("Closed cleanly:", manifest.get("closed_cleanly"))
        print("Writer queue pending:", manifest.get("writer_queue_pending"))

        print("\nRegistered callbacks:")
        for item in manifest.get("registered_callbacks", []):
            print("  ", item)

        print("\nUnavailable callbacks:")
        unavailable = manifest.get("unavailable_callbacks", [])
        if unavailable:
            for item in unavailable:
                print("  ", item)
        else:
            print("  none")

    counts = dict(manifest.get("counts", {}))
    streams_dir = session / "streams"
    jsonl_files = sorted(streams_dir.glob("*.jsonl")) if streams_dir.exists() else []
    if (not counts or not any(int(value) > 0 for value in counts.values())) and not args.no_fallback_count:
        print("\nManifest counts are absent or empty; counting JSONL lines...")
        counts = {path.stem: count_jsonl(path) for path in jsonl_files}

    print("\nSample counts:")
    if counts:
        for key, value in sorted(counts.items()):
            print(f"  {key}: {value}")
    else:
        print("  none")

    print("\nDropped JSONL events:")
    dropped = manifest.get("dropped_jsonl_events", {})
    if not dropped or not any(int(value) for value in dropped.values()):
        print("  none")
    else:
        for key, value in sorted(dropped.items()):
            print(f"  {key}: {value}")

    snapshots = sorted((session / "query_snapshots").glob("*.json")) if (session / "query_snapshots").exists() else []
    print(f"\nQuery snapshots: {len(snapshots)}")

    vrs_files = sorted(session.rglob("*.vrs"))
    print(f"VRS files: {len(vrs_files)}")
    for path in vrs_files:
        print(f"  {path.relative_to(session)} ({human_bytes(path.stat().st_size)})")

    print("\nFiles:")
    for path in sorted(session.rglob("*")):
        if path.is_file():
            print(f"  {path.relative_to(session)} ({human_bytes(path.stat().st_size)})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
