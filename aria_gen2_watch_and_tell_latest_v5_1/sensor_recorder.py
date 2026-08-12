from __future__ import annotations

import copy
import json
import math
import queue
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

import numpy as np


def _now_ns() -> int:
    return time.time_ns()


def _iso_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _call_zero_arg(value: Any) -> Any:
    if callable(value):
        try:
            return value()
        except TypeError:
            return value
        except Exception:
            return None
    return value


def _to_jsonable(value: Any, depth: int = 0) -> Any:
    """Best-effort conversion for pybind11 SDK objects.

    The implementation deliberately avoids traversing private fields and limits
    recursion so an unexpected SDK object cannot explode the log size.
    """
    if depth > 5:
        return str(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (list, tuple, set)):
        return [_to_jsonable(v, depth + 1) for v in value]
    if isinstance(value, dict):
        return {str(k): _to_jsonable(v, depth + 1) for k, v in value.items()}
    if hasattr(value, "total_seconds"):
        try:
            return float(value.total_seconds())
        except Exception:
            pass
    if hasattr(value, "translation") and hasattr(value, "rotation"):
        try:
            t = _call_zero_arg(getattr(value, "translation"))
            r_obj = _call_zero_arg(getattr(value, "rotation"))
            r = _call_zero_arg(getattr(r_obj, "log", None)) if r_obj is not None else None
            return {
                "translation": _to_jsonable(t, depth + 1),
                "rotation_log": _to_jsonable(r, depth + 1),
            }
        except Exception:
            pass
    if hasattr(value, "__dict__"):
        try:
            return {
                str(k): _to_jsonable(v, depth + 1)
                for k, v in vars(value).items()
                if not str(k).startswith("_")
            }
        except Exception:
            pass

    # Probe known public SDK-style attributes. This is intentionally broad to
    # remain compatible across Client SDK versions.
    names = (
        "capture_timestamp_ns", "tracking_timestamp", "tracking_timestamp_ns",
        "timestamp_ns", "utc_timestamp_ns", "sensor_timestamp_ns",
        "accel_msec2", "gyro_radsec", "mag_tesla", "temperature",
        "pressure", "latitude", "longitude", "altitude", "accuracy",
        "speed", "bearing", "value", "values", "confidence", "quality",
        "yaw", "pitch", "depth", "vergence_left_yaw", "vergence_right_yaw",
        "left_hand", "right_hand", "left_hand_pose", "right_hand_pose",
        "transform_odometry_bodyimu", "transform_odometry_device",
        "velocity_device", "angular_velocity_device", "gravity_odometry",
        "unique_id", "rssi", "ssid", "frequency", "channel",
        "ambient_light", "lux", "proximity", "sample_rate",
    )
    out: dict[str, Any] = {}
    for name in names:
        try:
            if hasattr(value, name):
                v = _call_zero_arg(getattr(value, name))
                if v is not None:
                    out[name] = _to_jsonable(v, depth + 1)
        except Exception:
            continue
    if out:
        return out
    return str(value)


def _get(obj: Any, *names: str) -> Any:
    for name in names:
        try:
            if hasattr(obj, name):
                value = _call_zero_arg(getattr(obj, name))
                if value is not None:
                    return value
        except Exception:
            continue
    return None


def _vector(value: Any) -> Optional[list[float]]:
    if value is None:
        return None
    try:
        arr = np.asarray(value, dtype=float).reshape(-1)
        if arr.size:
            return [float(x) for x in arr]
    except Exception:
        pass
    vals = []
    for key in ("x", "y", "z", "w"):
        try:
            if hasattr(value, key):
                vals.append(float(_call_zero_arg(getattr(value, key))))
        except Exception:
            pass
    return vals or None


def _timestamp_ns(payload: Any) -> int:
    value = _get(
        payload,
        "capture_timestamp_ns",
        "tracking_timestamp_ns",
        "timestamp_ns",
        "sensor_timestamp_ns",
        "utc_timestamp_ns",
    )
    if value is None:
        ts = _get(payload, "tracking_timestamp")
        if ts is not None and hasattr(ts, "total_seconds"):
            try:
                return int(float(ts.total_seconds()) * 1e9)
            except Exception:
                pass
        return _now_ns()
    try:
        return int(value)
    except Exception:
        return _now_ns()


@dataclass
class SensorEvent:
    stream: str
    timestamp_ns: int
    received_utc: str
    payload: dict[str, Any]
    device_id: Optional[str] = None


class SensorRecorder:
    """Thread-safe live sensor state + continuous JSONL recorder.

    Raw streamed packets should additionally be recorded to VRS through the
    StreamReceiver. JSONL contains decoded callback values for easy analysis.
    """

    def __init__(
        self,
        base_dir: Path,
        user_id: str,
        enabled: bool = True,
        rolling_seconds: float = 45.0,
        queue_size: int = 100_000,
        manifest_interval_seconds: float = 5.0,
        ppg_window_seconds: float = 30.0,
        ppg_min_duration_seconds: float = 30.0,
        ppg_default_sample_rate: float = 128.0,
        ppg_motion_gyro_threshold: float = 0.35,
        ppg_peak_ratio_threshold: float = 4.0,
    ) -> None:
        self.enabled = enabled
        self.user_id = user_id
        self.base_dir = Path(base_dir).expanduser().resolve()
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = self.base_dir / "sensors" / f"{user_id}_{self.session_id}"
        self.stream_dir = self.session_dir / "streams"
        self.snapshot_dir = self.session_dir / "query_snapshots"
        self.manifest_path = self.session_dir / "manifest.json"
        self.rolling_seconds = max(float(rolling_seconds), float(ppg_window_seconds) + 5.0)
        self.manifest_interval_seconds = max(1.0, float(manifest_interval_seconds))
        self.ppg_window_seconds = max(10.0, float(ppg_window_seconds))
        self.ppg_min_duration_seconds = max(10.0, float(ppg_min_duration_seconds))
        self.ppg_default_sample_rate = max(1.0, float(ppg_default_sample_rate))
        self.ppg_motion_gyro_threshold = max(0.01, float(ppg_motion_gyro_threshold))
        self.ppg_peak_ratio_threshold = max(1.0, float(ppg_peak_ratio_threshold))
        self._created_utc = _iso_utc()
        self._ended_utc: Optional[str] = None
        self._closed_cleanly = False
        self._lock = threading.Lock()
        self._close_lock = threading.Lock()
        self._manifest_lock = threading.Lock()
        self._latest: dict[str, dict[str, Any]] = {}
        self._counts: dict[str, int] = defaultdict(int)
        self._dropped: dict[str, int] = defaultdict(int)
        self._history: dict[str, deque[tuple[int, dict[str, Any]]]] = defaultdict(deque)
        self._registered: list[str] = []
        self._unavailable: list[str] = []
        self._q: queue.Queue[Optional[SensorEvent]] = queue.Queue(maxsize=queue_size)
        self._stop = threading.Event()
        self._writer: Optional[threading.Thread] = None
        self._manifest_stop = threading.Event()
        self._manifest_writer: Optional[threading.Thread] = None
        self._files: dict[str, Any] = {}
        self._accepting = True
        self._closed = False

        if self.enabled:
            self.stream_dir.mkdir(parents=True, exist_ok=True)
            self.snapshot_dir.mkdir(parents=True, exist_ok=True)
            self._writer = threading.Thread(
                target=self._writer_loop,
                name="aria-sensor-jsonl-writer",
                daemon=True,
            )
            self._writer.start()
            self._manifest_writer = threading.Thread(
                target=self._manifest_loop,
                name="aria-sensor-manifest-writer",
                daemon=True,
            )
            self._manifest_writer.start()
            self._write_manifest()

    @property
    def vrs_path(self) -> Path:
        return self.session_dir / f"{self.user_id}_{self.session_id}_all_streams.vrs"

    def mark_registered(self, name: str) -> None:
        with self._lock:
            self._registered.append(name)
        self._write_manifest()

    def mark_unavailable(self, name: str) -> None:
        with self._lock:
            self._unavailable.append(name)
        self._write_manifest()

    def _write_manifest(self) -> None:
        if not self.enabled:
            return
        with self._manifest_lock:
            with self._lock:
                manifest = {
                    "session_id": self.session_id,
                    "user_id": self.user_id,
                    "created_utc": self._created_utc,
                    "ended_utc": self._ended_utc,
                    "closed_cleanly": self._closed_cleanly,
                    "registered_callbacks": sorted(set(self._registered)),
                    "unavailable_callbacks": sorted(set(self._unavailable)),
                    "counts": dict(self._counts),
                    "dropped_jsonl_events": dict(self._dropped),
                    "writer_queue_pending": int(getattr(self._q, "unfinished_tasks", 0)),
                    "vrs_path": str(self.vrs_path),
                    "ppg_analysis": {
                        "window_seconds": self.ppg_window_seconds,
                        "minimum_duration_seconds": self.ppg_min_duration_seconds,
                        "default_sample_rate_hz": self.ppg_default_sample_rate,
                        "motion_gyro_threshold_rad_s_rms": self.ppg_motion_gyro_threshold,
                        "spectral_peak_ratio_threshold": self.ppg_peak_ratio_threshold,
                    },
                    "note": "VRS is the authoritative raw stream record; JSONL stores decoded callback values.",
                }
            temp_path = self.manifest_path.with_suffix(".json.tmp")
            temp_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            temp_path.replace(self.manifest_path)

    def _manifest_loop(self) -> None:
        while not self._manifest_stop.wait(self.manifest_interval_seconds):
            try:
                self._write_manifest()
            except Exception:
                pass

    def _writer_loop(self) -> None:
        while not self._stop.is_set() or not self._q.empty():
            try:
                event = self._q.get(timeout=0.25)
            except queue.Empty:
                continue
            if event is None:
                self._q.task_done()
                break
            try:
                fh = self._files.get(event.stream)
                if fh is None:
                    path = self.stream_dir / f"{event.stream}.jsonl"
                    fh = path.open("a", encoding="utf-8", buffering=1)
                    self._files[event.stream] = fh
                row = {
                    "stream": event.stream,
                    "timestamp_ns": event.timestamp_ns,
                    "received_utc": event.received_utc,
                    "device_id": event.device_id,
                    "payload": event.payload,
                }
                fh.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
            finally:
                self._q.task_done()

    def close(self, timeout_seconds: float = 20.0) -> None:
        if not self.enabled:
            return
        with self._close_lock:
            if self._closed:
                return
            self._closed = True
            self._accepting = False

        deadline = time.monotonic() + max(1.0, float(timeout_seconds))
        # Allow the JSONL writer to drain all events accepted before callbacks
        # were cleared. The periodic manifest already checkpoints counts in case
        # native shutdown terminates unexpectedly.
        while getattr(self._q, "unfinished_tasks", 0) > 0 and time.monotonic() < deadline:
            time.sleep(0.05)

        self._stop.set()
        try:
            self._q.put_nowait(None)
        except queue.Full:
            pass
        if self._writer is not None:
            remaining = max(0.5, deadline - time.monotonic())
            self._writer.join(timeout=remaining)

        for fh in self._files.values():
            try:
                fh.flush()
                fh.close()
            except Exception:
                pass

        self._manifest_stop.set()
        if self._manifest_writer is not None:
            self._manifest_writer.join(timeout=2.0)

        self._ended_utc = _iso_utc()
        self._closed_cleanly = getattr(self._q, "unfinished_tasks", 0) == 0
        self._write_manifest()

    def record(self, stream: str, payload: dict[str, Any], timestamp_ns: Optional[int] = None, device_id: Optional[str] = None) -> None:
        if not self._accepting:
            return
        ts = int(timestamp_ns or _now_ns())
        safe = _to_jsonable(payload)
        if not isinstance(safe, dict):
            safe = {"value": safe}
        with self._lock:
            self._latest[stream] = {"timestamp_ns": ts, "payload": copy.deepcopy(safe)}
            self._counts[stream] += 1
            hist = self._history[stream]
            hist.append((ts, copy.deepcopy(safe)))
            cutoff = ts - int(self.rolling_seconds * 1e9)
            while hist and hist[0][0] < cutoff:
                hist.popleft()
        if self.enabled:
            event = SensorEvent(stream, ts, _iso_utc(), safe, device_id)
            try:
                self._q.put_nowait(event)
            except queue.Full:
                with self._lock:
                    self._dropped[stream] += 1

    def snapshot(self, window_seconds: float = 10.0) -> dict[str, Any]:
        now = _now_ns()
        analysis_window = max(float(window_seconds), self.ppg_window_seconds + 2.0)
        cutoff = now - int(analysis_window * 1e9)
        with self._lock:
            latest = copy.deepcopy(self._latest)
            counts = dict(self._counts)
            dropped = dict(self._dropped)
            history = {
                stream: [(ts, copy.deepcopy(payload)) for ts, payload in rows if ts >= cutoff]
                for stream, rows in self._history.items()
            }
        return {
            "snapshot_utc": _iso_utc(),
            "snapshot_timestamp_ns": now,
            "window_seconds": window_seconds,
            "analysis_window_seconds": analysis_window,
            "latest": latest,
            "sample_counts_session": counts,
            "dropped_jsonl_events": dropped,
            "summaries": self._summaries(history),
        }

    def save_snapshot(self, snapshot: dict[str, Any], record_id: str) -> str:
        if not self.enabled:
            return ""
        path = self.snapshot_dir / f"{self.user_id}_{record_id}.json"
        path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
        return str(path)

    @staticmethod
    def _extract_numeric(rows: list[tuple[int, dict[str, Any]]], keys: tuple[str, ...]) -> list[tuple[int, float]]:
        out: list[tuple[int, float]] = []
        for ts, payload in rows:
            for key in keys:
                value = payload.get(key)
                if isinstance(value, (int, float)) and math.isfinite(float(value)):
                    out.append((ts, float(value)))
                    break
        return out

    @staticmethod
    def _imu_metrics(rows: list[tuple[int, dict[str, Any]]]) -> dict[str, float]:
        accel_norms: list[float] = []
        gyro_norms: list[float] = []
        for _, payload in rows:
            accel = payload.get("accel_msec2") or payload.get("accel_m_s2") or payload.get("accel")
            gyro = payload.get("gyro_radsec") or payload.get("gyro_rad_s") or payload.get("gyro")
            try:
                if accel is not None:
                    accel_norms.append(float(np.linalg.norm(np.asarray(accel, dtype=float))))
                if gyro is not None:
                    gyro_norms.append(float(np.linalg.norm(np.asarray(gyro, dtype=float))))
            except Exception:
                continue
        result: dict[str, float] = {}
        if accel_norms:
            result["accel_norm_mean"] = float(np.mean(accel_norms))
            result["accel_norm_std"] = float(np.std(accel_norms))
        if gyro_norms:
            result["gyro_norm_mean"] = float(np.mean(gyro_norms))
            result["gyro_norm_std"] = float(np.std(gyro_norms))
            result["movement_intensity"] = float(np.sqrt(np.mean(np.square(gyro_norms))))
        return result

    def _summaries(self, history: dict[str, list[tuple[int, dict[str, Any]]]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        movement_values: list[float] = []

        for stream, rows in history.items():
            if stream.startswith("imu"):
                summary: dict[str, Any] = {"samples_in_window": len(rows)}
                summary.update(self._imu_metrics(rows))
                if summary.get("movement_intensity") is not None:
                    movement_values.append(float(summary["movement_intensity"]))
                result[stream] = summary

        movement_intensity = float(np.mean(movement_values)) if movement_values else None

        for stream, rows in history.items():
            if stream.startswith("imu"):
                continue
            summary = {"samples_in_window": len(rows)}
            if stream == "ppg":
                values = self._extract_numeric(rows, ("value", "ppg", "signal"))
                if values:
                    x = np.asarray([value for _, value in values], dtype=float)
                    summary.update({
                        "mean": float(np.mean(x)),
                        "std": float(np.std(x)),
                        "min": float(np.min(x)),
                        "max": float(np.max(x)),
                    })
                    quality = self._experimental_bpm(values, movement_intensity)
                    summary.update(quality)
            elif stream in ("eye_gaze", "vio", "hand_pose", "barometer", "magnetometer", "gps", "phone_location"):
                if rows:
                    summary["latest"] = rows[-1][1]
            result[stream] = summary
        return result

    def _experimental_bpm(
        self,
        samples: list[tuple[int, float]],
        movement_intensity: Optional[float],
    ) -> dict[str, Any]:
        result: dict[str, Any] = {
            "pulse_status": "insufficient_data",
            "experimental_bpm_warning": "Research-only estimate; not a medical measurement.",
        }
        if len(samples) < 30:
            return result

        t = np.asarray([ts for ts, _ in samples], dtype=float) / 1e9
        y = np.asarray([value for _, value in samples], dtype=float)
        order = np.argsort(t)
        t, y = t[order], y[order]
        finite = np.isfinite(t) & np.isfinite(y)
        t, y = t[finite], y[finite]
        if len(t) < 30:
            return result

        duration = float(t[-1] - t[0])
        result["duration_seconds"] = duration
        if duration < self.ppg_min_duration_seconds:
            result["pulse_status"] = "need_longer_window"
            return result

        if movement_intensity is not None:
            result["motion_gyro_rms_rad_s"] = movement_intensity
            if movement_intensity > self.ppg_motion_gyro_threshold:
                result["pulse_status"] = "rejected_due_to_motion"
                return result

        dt = np.diff(t)
        dt = dt[np.isfinite(dt) & (dt > 0)]
        if dt.size:
            inferred_fs = float(1.0 / np.median(dt))
        else:
            inferred_fs = self.ppg_default_sample_rate
        # Protect against callback timestamps that represent packet rather than
        # sample cadence. The device specification is used only as a fallback.
        fs = inferred_fs if 5.0 <= inferred_fs <= 512.0 else self.ppg_default_sample_rate
        result["sample_rate_hz"] = fs

        sample_count = max(32, int(round(duration * fs)) + 1)
        uniform_t = np.linspace(t[0], t[-1], sample_count)
        y = np.interp(uniform_t, t, y)
        if float(np.std(y)) <= 1e-9:
            result["pulse_status"] = "flat_signal"
            return result

        # Linear detrending and Hann taper reduce leakage without requiring SciPy.
        x_axis = np.linspace(-1.0, 1.0, len(y))
        slope, intercept = np.polyfit(x_axis, y, 1)
        y = y - (slope * x_axis + intercept)
        y = y * np.hanning(len(y))
        spectrum = np.abs(np.fft.rfft(y))
        frequencies = np.fft.rfftfreq(len(y), d=1.0 / fs)
        band = (frequencies >= 0.7) & (frequencies <= 3.0)
        if not np.any(band):
            result["pulse_status"] = "frequency_band_unavailable"
            return result

        band_spectrum = spectrum[band]
        band_frequencies = frequencies[band]
        peak_index = int(np.argmax(band_spectrum))
        peak_value = float(band_spectrum[peak_index])
        noise_floor = float(np.median(band_spectrum)) + 1e-12
        peak_ratio = peak_value / noise_floor
        bpm = float(band_frequencies[peak_index] * 60.0)
        result["spectral_peak_ratio"] = peak_ratio

        if not (42.0 <= bpm <= 180.0):
            result["pulse_status"] = "outside_plausible_range"
            return result
        if peak_ratio < self.ppg_peak_ratio_threshold:
            result["pulse_status"] = "low_spectral_confidence"
            return result

        confidence = min(1.0, max(0.0, (peak_ratio - self.ppg_peak_ratio_threshold) / (2.0 * self.ppg_peak_ratio_threshold)))
        result.update({
            "pulse_status": "research_estimate_available",
            "experimental_bpm": round(bpm, 1),
            "pulse_confidence_0_1": round(confidence, 3),
        })
        return result

    @staticmethod
    def _numbers(value: Any, limit: int = 3) -> list[float]:
        found: list[float] = []
        def walk(item: Any) -> None:
            if len(found) >= limit:
                return
            if isinstance(item, (int, float)) and math.isfinite(float(item)):
                found.append(float(item))
            elif isinstance(item, dict):
                for child in item.values():
                    walk(child)
                    if len(found) >= limit:
                        return
            elif isinstance(item, (list, tuple)):
                for child in item:
                    walk(child)
                    if len(found) >= limit:
                        return
        walk(value)
        return found

    @staticmethod
    def _fmt(value: Any, digits: int = 3) -> str:
        try:
            return f"{float(value):.{digits}f}"
        except (TypeError, ValueError):
            return "n/a"

    def model_context(self, snapshot: dict[str, Any], max_chars: int = 500) -> str:
        latest = snapshot.get("latest", {})
        summaries = snapshot.get("summaries", {})
        parts: list[str] = []

        gaze = latest.get("eye_gaze", {}).get("payload")
        if gaze:
            parts.append(
                f"Gaze yaw={self._fmt(gaze.get('yaw'))} rad, "
                f"pitch={self._fmt(gaze.get('pitch'))} rad, "
                f"depth={self._fmt(gaze.get('depth'), 2)} m."
            )

        hand = latest.get("hand_pose", {}).get("payload")
        if hand:
            left = hand.get("left_hand") is not None
            right = hand.get("right_hand") is not None
            parts.append(f"Hands detected: left={left}, right={right}.")

        vio = latest.get("vio", {}).get("payload")
        if vio:
            pose = vio.get("pose") or {}
            translation = self._numbers(pose.get("translation") if isinstance(pose, dict) else pose, 3)
            rotation = self._numbers(pose.get("rotation_log") if isinstance(pose, dict) else None, 3)
            if translation:
                parts.append("Head position=" + ",".join(self._fmt(v) for v in translation) + " m.")
            if rotation:
                parts.append("Head rotation-log=" + ",".join(self._fmt(v) for v in rotation) + " rad.")

        imu_summaries = [value for key, value in summaries.items() if key.startswith("imu")]
        movement = [value.get("movement_intensity") for value in imu_summaries if value.get("movement_intensity") is not None]
        if movement:
            parts.append(f"Head-motion RMS={float(np.mean(movement)):.3f} rad/s.")

        ppg = summaries.get("ppg")
        if ppg:
            status = ppg.get("pulse_status", "recording")
            if ppg.get("experimental_bpm") is not None:
                parts.append(
                    f"Research PPG estimate={ppg['experimental_bpm']} bpm "
                    f"(confidence={ppg.get('pulse_confidence_0_1', 'n/a')}; non-medical)."
                )
            else:
                parts.append(f"PPG recorded; pulse status={status} (non-medical).")

        barometer = latest.get("barometer", {}).get("payload")
        if barometer:
            parts.append(
                f"Pressure={self._fmt(barometer.get('pressure'), 1)} Pa; "
                f"temperature={self._fmt(barometer.get('temperature'), 1)} C."
            )

        selected: list[str] = []
        length = 0
        for part in parts:
            extra = len(part) + (1 if selected else 0)
            if length + extra > max_chars:
                break
            selected.append(part)
            length += extra
        return " ".join(selected)

    # ---- callback factories -------------------------------------------------
    def callbacks(self) -> dict[str, Callable[..., None]]:
        return {
            "register_imu_callback": self._imu_callback,
            "register_eye_gaze_callback": self._eye_gaze_callback,
            "register_hand_pose_callback": self._hand_pose_callback,
            "register_vio_callback": self._vio_callback,
            "register_vio_high_frequency_callback": self._vio_hf_callback,
            "register_barometer_callback": self._barometer_callback,
            "register_magnetometer_callback": self._magnetometer_callback,
            "register_gps_callback": self._gps_callback,
            "register_phone_location_callback": self._phone_location_callback,
            "register_ppg_callback": self._ppg_callback,
            "register_bluetooth_beacon_callback": self._ble_callback,
            "register_wifi_beacon_callback": self._wifi_callback,
            "register_device_calib_callback": self._calibration_callback,
        }

    @staticmethod
    def _device_id(kwargs: dict[str, Any]) -> Optional[str]:
        value = kwargs.get("device_id")
        return str(value) if value else None

    def _imu_callback(self, motion_data: Any, sensor_label: str = "imu", **kwargs: Any) -> None:
        payload = {
            "sensor_label": str(sensor_label),
            "accel_msec2": _vector(_get(motion_data, "accel_msec2", "accel_m_s2", "accelerometer")),
            "gyro_radsec": _vector(_get(motion_data, "gyro_radsec", "gyro_rad_s", "gyroscope")),
            "temperature": _get(motion_data, "temperature"),
            "raw": _to_jsonable(motion_data),
        }
        self.record(f"imu_{sensor_label}", payload, _timestamp_ns(motion_data), self._device_id(kwargs))

    def _eye_gaze_callback(self, data: Any, **kwargs: Any) -> None:
        payload = {
            "yaw": _get(data, "yaw"), "pitch": _get(data, "pitch"), "depth": _get(data, "depth"),
            "vergence_left_yaw": _get(data, "vergence_left_yaw"),
            "vergence_right_yaw": _get(data, "vergence_right_yaw"),
            "raw": _to_jsonable(data),
        }
        self.record("eye_gaze", payload, _timestamp_ns(data), self._device_id(kwargs))

    @staticmethod
    def _hand_summary(hand: Any) -> Optional[dict[str, Any]]:
        if hand is None:
            return None
        normals = _get(hand, "wrist_and_palm_normal_device")
        return {
            "confidence": _get(hand, "confidence"),
            "wrist_position_device": _vector(_get(hand, "get_wrist_position_device", "wrist_position_device")),
            "palm_position_device": _vector(_get(hand, "get_palm_position_device", "palm_position_device")),
            "wrist_normal_device": _vector(_get(normals, "wrist_normal_device")) if normals is not None else None,
            "palm_normal_device": _vector(_get(normals, "palm_normal_device")) if normals is not None else None,
        }

    def _hand_pose_callback(self, data: Any, **kwargs: Any) -> None:
        left_raw = _get(data, "left_hand", "left_hand_pose")
        right_raw = _get(data, "right_hand", "right_hand_pose")
        payload = {
            "left_hand": self._hand_summary(left_raw),
            "right_hand": self._hand_summary(right_raw),
            "raw": _to_jsonable(data),
        }
        self.record("hand_pose", payload, _timestamp_ns(data), self._device_id(kwargs))

    def _vio_callback(self, data: Any, **kwargs: Any) -> None:
        pose = _get(data, "transform_odometry_bodyimu", "transform_odometry_device", "pose")
        payload = {
            "pose": _to_jsonable(pose),
            "velocity_device": _vector(_get(data, "velocity_device", "linear_velocity", "velocity")),
            "angular_velocity_device": _vector(_get(data, "angular_velocity_device", "angular_velocity")),
            "gravity_odometry": _vector(_get(data, "gravity_odometry")),
            "raw": _to_jsonable(data),
        }
        self.record("vio", payload, _timestamp_ns(data), self._device_id(kwargs))

    def _vio_hf_callback(self, data: Any, **kwargs: Any) -> None:
        payload = {"raw": _to_jsonable(data)}
        self.record("vio_high_frequency", payload, _timestamp_ns(data), self._device_id(kwargs))

    def _barometer_callback(self, data: Any, **kwargs: Any) -> None:
        payload = {"pressure": _get(data, "pressure"), "temperature": _get(data, "temperature"), "raw": _to_jsonable(data)}
        self.record("barometer", payload, _timestamp_ns(data), self._device_id(kwargs))

    def _magnetometer_callback(self, data: Any, sensor_label: str = "magnetometer", **kwargs: Any) -> None:
        payload = {"sensor_label": str(sensor_label), "mag_tesla": _vector(_get(data, "mag_tesla", "magnetic_field")), "raw": _to_jsonable(data)}
        self.record("magnetometer", payload, _timestamp_ns(data), self._device_id(kwargs))

    def _gps_callback(self, data: Any, **kwargs: Any) -> None:
        self.record("gps", _to_jsonable(data), _timestamp_ns(data), self._device_id(kwargs))

    def _phone_location_callback(self, data: Any, **kwargs: Any) -> None:
        self.record("phone_location", _to_jsonable(data), _timestamp_ns(data), self._device_id(kwargs))

    def _ppg_callback(self, data: Any, **kwargs: Any) -> None:
        raw_payload = _to_jsonable(data)
        value = _get(data, "value", "ppg", "signal")
        payload: dict[str, Any] = {
            "value": float(value) if isinstance(value, (int, float, np.generic)) else value,
            "sample_rate": _get(data, "sample_rate"),
            "raw": raw_payload,
        }
        self.record("ppg", payload, _timestamp_ns(data), self._device_id(kwargs))

    def _ble_callback(self, data: Any, **kwargs: Any) -> None:
        self.record("bluetooth_beacons", {"beacons": _to_jsonable(data)}, _now_ns(), self._device_id(kwargs))

    def _wifi_callback(self, data: Any, **kwargs: Any) -> None:
        self.record("wifi_beacons", {"beacons": _to_jsonable(data)}, _now_ns(), self._device_id(kwargs))

    def _calibration_callback(self, data: Any, **kwargs: Any) -> None:
        self.record("device_calibration", {"calibration": _to_jsonable(data)}, _now_ns(), self._device_id(kwargs))
