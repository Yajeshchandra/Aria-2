from __future__ import annotations

import ast
import json
import math
import re
import tempfile
import time
from pathlib import Path

from sensor_recorder import SensorRecorder


def load_main_constants() -> dict[str, object]:
    source = Path(__file__).with_name("watch_and_tell_aria_gen2.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    wanted = {"WAKE_VARIANTS", "WAKE_PATTERN", "VISION_HINTS"}
    nodes = []
    for node in tree.body:
        targets = []
        if isinstance(node, ast.Assign):
            targets = [target.id for target in node.targets if isinstance(target, ast.Name)]
        if any(name in wanted for name in targets):
            nodes.append(node)
    namespace = {"re": re}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "watch_and_tell_constants", "exec"), namespace)
    return namespace


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
    context = recorder.model_context(snapshot)
    assert len(context) <= 500


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


def test_wake_variants_and_pointing_vision() -> None:
    constants = load_main_constants()
    pattern = constants["WAKE_PATTERN"]
    for phrase in (
        "Hey Meta, what is this?",
        "Hey Mera, what am I pointing at?",
        "Hey Mana what am I looking at?",
        "Hey Mehta, what is your name?",
    ):
        assert pattern.search(phrase), phrase
    assert not pattern.search("What am I pointing at?"), "Non-wake speech must not match"
    hints = constants["VISION_HINTS"]
    assert "what am i pointing at" in hints
    assert "what am i holding" in hints


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
    test_wake_variants_and_pointing_vision()
    test_manifest_finalization()
    print("V5.1 synthetic tests passed.")
