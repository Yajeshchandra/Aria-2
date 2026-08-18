from __future__ import annotations

import json
import math
import tempfile
import time
from pathlib import Path

from sensor_recorder import SensorRecorder


def test_ppg_estimate() -> None:
    recorder = SensorRecorder(
        base_dir=Path(tempfile.mkdtemp()),
        user_id="TEST",
        enabled=False,
        rolling_seconds=45,
        ppg_window_seconds=30,
        ppg_min_duration_seconds=30,
        ppg_default_sample_rate=128,
        ppg_motion_gyro_threshold=0.35,
        ppg_peak_ratio_threshold=4.0,
    )
    fs = 128.0
    duration = 32.0
    bpm_expected = 72.0
    frequency = bpm_expected / 60.0
    end_ns = time.time_ns()
    start_ns = end_ns - int(duration * 1e9)
    total = int(duration * fs) + 1
    for index in range(total):
        t = index / fs
        ts = start_ns + int(t * 1e9)
        value = 1000.0 + 30.0 * math.sin(2.0 * math.pi * frequency * t)
        recorder.record("ppg", {"value": value}, ts)
        recorder.record(
            "imu_imu-left",
            {"accel_msec2": [0.0, 0.0, 9.81], "gyro_radsec": [0.01, 0.01, 0.01]},
            ts,
        )
    snapshot = recorder.snapshot(10.0)
    ppg = snapshot["summaries"]["ppg"]
    assert ppg["pulse_status"] == "research_estimate_available", ppg
    assert abs(ppg["experimental_bpm"] - bpm_expected) <= 2.0, ppg


def test_motion_rejection() -> None:
    recorder = SensorRecorder(
        base_dir=Path(tempfile.mkdtemp()),
        user_id="TEST",
        enabled=False,
        rolling_seconds=45,
        ppg_window_seconds=30,
        ppg_min_duration_seconds=30,
    )
    fs = 128.0
    duration = 31.0
    end_ns = time.time_ns()
    start_ns = end_ns - int(duration * 1e9)
    for index in range(int(duration * fs) + 1):
        t = index / fs
        ts = start_ns + int(t * 1e9)
        recorder.record("ppg", {"value": 1000 + 20 * math.sin(2 * math.pi * 1.2 * t)}, ts)
        recorder.record(
            "imu_imu-left",
            {"accel_msec2": [0.0, 0.0, 9.81], "gyro_radsec": [1.0, 0.5, 0.2]},
            ts,
        )
    ppg = recorder.snapshot(10.0)["summaries"]["ppg"]
    assert ppg["pulse_status"] == "rejected_due_to_motion", ppg


def test_mixed_clock_origin_windowing() -> None:
    """Device timestamps on a different epoch than host time must not break windowing.

    Some Aria SDK builds/callbacks report boot-relative device timestamps
    rather than Unix-epoch ones. Before the received_ns fix (sensor_recorder.py,
    see HISTORY.md 2026-08-17), snapshot() compared these device timestamps
    directly against a host-time cutoff, which could silently filter out
    every sample while manifest.json still reported full counts. This test
    injects device timestamps on an unrelated, small, boot-relative-looking
    epoch and confirms the snapshot still reports the correct in-window
    count, since windowing now keys off received_ns (host clock, captured
    at record() call time), not the device-reported timestamp.
    """
    recorder = SensorRecorder(
        base_dir=Path(tempfile.mkdtemp()),
        user_id="TEST",
        enabled=False,
        rolling_seconds=45,
    )
    device_epoch_ns = 5_000_000_000  # ~5 seconds since an unrelated "boot" origin
    for index in range(10):
        recorder.record(
            "barometer",
            {"pressure": 90000 + index},
            timestamp_ns=device_epoch_ns + index * 1_000_000_000,
        )
    snapshot = recorder.snapshot(10.0)
    barometer = snapshot["summaries"]["barometer"]
    assert barometer["samples_in_window"] == 10, barometer


def test_qr_round_trip() -> None:
    """Ground truth for every scene/question boundary depends on this round-tripping cleanly."""
    import qrcode
    from pyzbar.pyzbar import decode as decode_qr_codes

    payload = "question:story_03_scene_2_q"
    image = qrcode.make(payload).convert("RGB")
    results = decode_qr_codes(image)
    assert len(results) == 1, results
    assert results[0].data.decode("utf-8") == payload


def test_manifest_finalization() -> None:
    base = Path(tempfile.mkdtemp())
    recorder = SensorRecorder(
        base_dir=base,
        user_id="TEST",
        enabled=True,
        rolling_seconds=45,
        manifest_interval_seconds=1,
    )
    for index in range(20):
        recorder.record("barometer", {"pressure": 90000 + index}, time.time_ns() + index)
    recorder.close(timeout_seconds=5)
    manifest = json.loads(recorder.manifest_path.read_text(encoding="utf-8"))
    assert manifest["counts"]["barometer"] == 20, manifest
    assert manifest["closed_cleanly"] is True, manifest
    assert manifest["ended_utc"], manifest
    jsonl = recorder.stream_dir / "barometer.jsonl"
    assert sum(1 for line in jsonl.open(encoding="utf-8") if line.strip()) == 20


if __name__ == "__main__":
    test_ppg_estimate()
    test_motion_rejection()
    test_mixed_clock_origin_windowing()
    test_qr_round_trip()
    test_manifest_finalization()
    print("V6 synthetic tests passed.")
