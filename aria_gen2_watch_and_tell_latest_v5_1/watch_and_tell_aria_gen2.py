from __future__ import annotations

import argparse
import base64
import csv
import io
import json
import os
import re
import signal
import sys
import tempfile
import threading
import time
import uuid
import wave
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image

from sensor_recorder import SensorRecorder

APP_DIR = Path(__file__).resolve().parent
ENV_FILE = APP_DIR / ".env"

import aria.sdk_gen2 as sdk_gen2
import aria.stream_receiver as receiver
from projectaria_tools.core.sensor_data import (
    AudioData,
    AudioDataRecord,
    ImageData,
    ImageDataRecord,
)


SAMPLE_RATE = 16_000
# A small, explicit set of observed transcription variants is accepted only
# when it follows the word "hey". This improves recall without matching
# arbitrary non-wake speech.
WAKE_VARIANTS = ("meta", "metta", "mehta", "mera", "mana", "meter")
WAKE_PATTERN = re.compile(
    r"\bhey[\s,.:;!?-]*(?:" + "|".join(re.escape(v) for v in WAKE_VARIANTS) + r")\b",
    re.IGNORECASE,
)
PROMPT_LEAK_PHRASES = (
    "the wearer may say",
    "the speaker may say",
    "wake phrase",
    "transcribe the complete question",
    "transcribe only clear english speech",
)
NO_SPEECH_MARKERS = (
    "no_speech",
    "no speech",
    "silence",
    "background noise",
    "noise only",
)
VISION_HINTS = (
    "watch and tell",
    "what am i looking at",
    "what do you see",
    "what is this",
    "what is that",
    "describe this",
    "describe what",
    "read this",
    "read the",
    "in front of me",
    "what's in front",
    "what is in front",
    "which object",
    "what color",
    "identify this object",
    "tell me about this",
    "what am i pointing at",
    "what are you pointing at",
    "what is being pointed at",
    "pointing at",
    "what am i holding",
    "what are you holding",
    "what is in my hand",
    "what is in my left hand",
    "what is in my right hand",
    "identify the object i am pointing at",
)


class AudioRingBuffer:
    """Thread-safe multichannel PCM ring buffer."""

    def __init__(self, sample_rate: int = SAMPLE_RATE, max_seconds: float = 20.0):
        self.sample_rate = sample_rate
        self.max_frames = int(sample_rate * max_seconds)
        self._chunks: deque[np.ndarray] = deque()
        self._total_frames = 0
        self._channels: Optional[int] = None
        self._lock = threading.Lock()

    @staticmethod
    def _to_pcm16(data: Any) -> tuple[np.ndarray, str]:
        """Convert SDK audio samples to signed 16-bit PCM without clipping sign bits.

        Some SDK/PyBind builds expose the underlying 16-bit PCM words through an
        unsigned NumPy dtype.  Numerically clipping such values maps every negative
        sample to +32767, producing an apparent ~31k RMS carrier.  Reinterpreting the
        low 16 bits restores the original two's-complement waveform.
        """
        raw = np.asarray(data)
        if raw.size == 0:
            return np.empty(0, dtype=np.int16), "empty"

        if np.issubdtype(raw.dtype, np.floating):
            pcm = (np.clip(raw, -1.0, 1.0) * 32767.0).astype(np.int16)
            return pcm, f"float-{raw.dtype}"

        if np.issubdtype(raw.dtype, np.unsignedinteger):
            # Preserve the low 16-bit two's-complement pattern instead of clipping.
            words = np.bitwise_and(raw.astype(np.uint64, copy=False), 0xFFFF)
            pcm = words.astype(np.uint16, copy=False).view(np.int16)
            return pcm, f"unsigned-low16-{raw.dtype}"

        if np.issubdtype(raw.dtype, np.signedinteger):
            if raw.dtype.itemsize == 2:
                return raw.astype(np.int16, copy=False), f"signed-{raw.dtype}"

            # Aria Gen 2 Python SDK builds may expose fixed-point PCM in int64.
            # On the user's SDK, values are exact multiples of 2^16, for example
            # -1114112 = -17 * 65536 and 1245184 = 19 * 65536.  These are signed
            # PCM samples stored in Q16 form, not full-scale int64 audio.  Recover
            # the waveform with an arithmetic right shift before converting.
            raw_min = int(raw.min())
            raw_max = int(raw.max())
            if raw_min < -32768 or raw_max > 32767:
                low16_zero = bool(np.all(np.bitwise_and(raw, 0xFFFF) == 0))
                if low16_zero:
                    shifted = np.right_shift(raw, 16)
                    pcm = np.clip(shifted, -32768, 32767).astype(np.int16)
                    return pcm, f"signed-q16-shift-{raw.dtype}"

            # Some PyBind builds instead preserve unsigned 16-bit PCM words in a
            # wider signed dtype.  Reinterpret those low bits without clipping.
            if raw_min >= 0 and raw_max <= 0xFFFF:
                words = np.bitwise_and(raw.astype(np.uint64, copy=False), 0xFFFF)
                pcm = words.astype(np.uint16, copy=False).view(np.int16)
                return pcm, f"signed-wide-low16-{raw.dtype}"

            # Genuine wider signed PCM values: clip only as a final fallback.
            pcm = np.clip(raw, -32768, 32767).astype(np.int16)
            return pcm, f"signed-clipped-{raw.dtype}"

        pcm = np.asarray(raw, dtype=np.int16)
        return pcm, f"fallback-{raw.dtype}"

    def append(self, data: Any, num_channels: int) -> tuple[str, int, int]:
        if num_channels <= 0:
            return "invalid-channels", 0, 0

        raw = np.asarray(data)
        if raw.size < num_channels:
            return "too-small", 0, 0

        pcm, conversion = self._to_pcm16(raw)
        usable = (pcm.size // num_channels) * num_channels
        frames = pcm[:usable].reshape(-1, num_channels).copy()

        with self._lock:
            if self._channels is not None and self._channels != num_channels:
                self._chunks.clear()
                self._total_frames = 0
            self._channels = num_channels
            self._chunks.append(frames)
            self._total_frames += len(frames)

            while self._chunks and self._total_frames > self.max_frames:
                excess = self._total_frames - self.max_frames
                first = self._chunks[0]
                if len(first) <= excess:
                    self._chunks.popleft()
                    self._total_frames -= len(first)
                else:
                    self._chunks[0] = first[excess:].copy()
                    self._total_frames -= excess

        return conversion, int(pcm.min(initial=0)), int(pcm.max(initial=0))

    def clear(self) -> None:
        with self._lock:
            self._chunks.clear()
            self._total_frames = 0

    def snapshot(self, seconds: float) -> Optional[np.ndarray]:
        wanted = max(1, int(self.sample_rate * seconds))
        with self._lock:
            if not self._chunks:
                return None
            merged = np.concatenate(list(self._chunks), axis=0)
        return merged[-wanted:].copy()


class SharedState:
    def __init__(self) -> None:
        self.audio = AudioRingBuffer()
        self._frame_lock = threading.Lock()
        self._latest_rgb: Optional[np.ndarray] = None
        self._latest_rgb_timestamp_ns: Optional[int] = None
        self.first_audio_seen = threading.Event()
        self.first_frame_seen = threading.Event()

    def set_rgb(self, frame: np.ndarray, timestamp_ns: int) -> None:
        with self._frame_lock:
            self._latest_rgb = frame.copy()
            self._latest_rgb_timestamp_ns = timestamp_ns
        self.first_frame_seen.set()

    def get_rgb(self) -> tuple[Optional[np.ndarray], Optional[int]]:
        with self._frame_lock:
            if self._latest_rgb is None:
                return None, None
            return self._latest_rgb.copy(), self._latest_rgb_timestamp_ns


class DataLogger:
    def __init__(self, base_dir: Path, user_id: str, enabled: bool):
        self.enabled = enabled
        self.user_id = user_id
        self.base_dir = base_dir.expanduser().resolve()
        self.images_dir = self.base_dir / "images"
        self.audio_dir = self.base_dir / "audio"
        self.responses_dir = self.base_dir / "responses"
        self.csv_path = self.base_dir / "watch_and_tell_log.csv"
        self._lock = threading.Lock()

        if self.enabled:
            self.images_dir.mkdir(parents=True, exist_ok=True)
            self.audio_dir.mkdir(parents=True, exist_ok=True)
            self.responses_dir.mkdir(parents=True, exist_ok=True)
            self._ensure_header()

    def _ensure_header(self) -> None:
        if self.csv_path.exists():
            return
        with self.csv_path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(
                [
                    "record_id",
                    "user_id",
                    "timestamp_local",
                    "timestamp_utc",
                    "query",
                    "mode",
                    "vision_used",
                    "image_path",
                    "audio_path",
                    "answer",
                    "model",
                    "latency_ms",
                    "status",
                    "error",
                    "sources_json",
                    "response_json_path",
                    "sensor_snapshot_path",
                    "sensor_context",
                ]
            )

    @staticmethod
    def _stamp() -> str:
        return datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    def save_image(self, image_bytes: bytes, record_id: str) -> str:
        if not self.enabled:
            return ""
        path = self.images_dir / f"{self.user_id}_{self._stamp()}_{record_id}.jpg"
        path.write_bytes(image_bytes)
        return str(path)

    def save_audio(self, wav_bytes: bytes, record_id: str) -> str:
        if not self.enabled:
            return ""
        path = self.audio_dir / f"{self.user_id}_{self._stamp()}_{record_id}.wav"
        path.write_bytes(wav_bytes)
        return str(path)

    def save_response(self, response_json: str, record_id: str) -> str:
        if not self.enabled or not response_json:
            return ""
        path = self.responses_dir / f"{self.user_id}_{self._stamp()}_{record_id}.json"
        path.write_text(response_json, encoding="utf-8")
        return str(path)

    def append_row(self, row: dict[str, Any]) -> None:
        if not self.enabled:
            return
        with self._lock, self.csv_path.open("a", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(
                [
                    row.get("record_id", ""),
                    self.user_id,
                    row.get("timestamp_local", ""),
                    row.get("timestamp_utc", ""),
                    row.get("query", ""),
                    row.get("mode", ""),
                    row.get("vision_used", False),
                    row.get("image_path", ""),
                    row.get("audio_path", ""),
                    row.get("answer", ""),
                    row.get("model", ""),
                    row.get("latency_ms", ""),
                    row.get("status", ""),
                    row.get("error", ""),
                    json.dumps(row.get("sources", []), ensure_ascii=False),
                    row.get("response_json_path", ""),
                    row.get("sensor_snapshot_path", ""),
                    row.get("sensor_context", ""),
                ]
            )


class WatchAndTellApp:
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.state = SharedState()
        self.client = OpenAI()
        self.device_client: Optional[Any] = None
        self.device: Optional[Any] = None
        self.stream_receiver: Optional[Any] = None
        self.running = True
        self.speaking_until = 0.0
        self._stopped = False
        self._stop_lock = threading.Lock()
        self._stop_requested = threading.Event()
        self._quit_thread: Optional[threading.Thread] = None
        self._audio_debug_printed = False

        data_dir = Path(os.getenv("WATCH_DATA_DIR", args.data_dir))
        user_id = args.user_id or os.getenv("WATCH_USER_ID") or self._persistent_user_id(data_dir)
        self.logger = DataLogger(data_dir, user_id, args.save_data)
        self.user_id = user_id
        self.sensors = SensorRecorder(
            base_dir=data_dir,
            user_id=user_id,
            enabled=args.save_sensors,
            rolling_seconds=args.sensor_rolling_seconds,
            manifest_interval_seconds=args.sensor_manifest_interval_seconds,
            ppg_window_seconds=args.ppg_window_seconds,
            ppg_min_duration_seconds=args.ppg_min_duration_seconds,
            ppg_default_sample_rate=args.ppg_default_sample_rate,
            ppg_motion_gyro_threshold=args.ppg_motion_gyro_threshold,
            ppg_peak_ratio_threshold=args.ppg_peak_ratio_threshold,
        )

    @staticmethod
    def _persistent_user_id(data_dir: Path) -> str:
        data_dir.mkdir(parents=True, exist_ok=True)
        id_file = data_dir / "user_id.txt"
        if id_file.exists():
            return id_file.read_text(encoding="utf-8").strip()
        new_id = f"user_{uuid.uuid4()}"
        id_file.write_text(new_id, encoding="utf-8")
        return new_id

    def rgb_callback(self, image_data: ImageData, image_record: ImageDataRecord) -> None:
        try:
            frame = image_data.to_numpy_array()
            self.state.set_rgb(frame, image_record.capture_timestamp_ns)
        except Exception as exc:
            print(f"[WARN] RGB callback error: {exc}")

    def audio_callback(
        self,
        audio_data: AudioData,
        audio_record: AudioDataRecord,
        num_channels: int,
    ) -> None:
        try:
            raw = np.asarray(audio_data.data)
            conversion, pcm_min, pcm_max = self.state.audio.append(
                audio_data.data, num_channels
            )
            if not self._audio_debug_printed:
                timestamps = getattr(audio_record, "capture_timestamps_ns", ())
                raw_min = int(raw.min()) if raw.size else 0
                raw_max = int(raw.max()) if raw.size else 0
                print(
                    "Audio format: "
                    f"raw_dtype={raw.dtype}, raw_values={raw.size}, "
                    f"channels={num_channels}, timestamps={len(timestamps)}, "
                    f"raw_min={raw_min}, raw_max={raw_max}, "
                    f"conversion={conversion}, pcm_min={pcm_min}, pcm_max={pcm_max}"
                )
                self._audio_debug_printed = True
            self.state.first_audio_seen.set()
        except Exception as exc:
            print(f"[WARN] Audio callback error: {exc}")

    def connect_and_stream(self) -> None:
        print("[1/4] Connecting to Aria Gen 2...")
        self.device_client = sdk_gen2.DeviceClient()
        config = sdk_gen2.DeviceClientConfig()
        legacy_serial_config = bool(
            self.args.serial and hasattr(config, "device_serial")
        )
        if legacy_serial_config:
            config.device_serial = self.args.serial
        self.device_client.set_client_config(config)

        if self.args.serial and not legacy_serial_config and hasattr(sdk_gen2, "DeviceTarget"):
            target = sdk_gen2.DeviceTarget(serial=self.args.serial)
            self.device = self.device_client.connect(target)
        else:
            self.device = self.device_client.connect()
        print(f"Connected: {self.device.connection_id()}")

        print(f"[2/4] Starting stream with profile: {self.args.profile}")
        streaming_config = sdk_gen2.HttpStreamingConfig()
        streaming_config.profile_name = self.args.profile
        self.device.set_streaming_config(streaming_config)
        self.device.start_streaming()

        print(f"[3/4] Starting receiver on 0.0.0.0:{self.args.port}")
        server_config = sdk_gen2.HttpServerConfig()
        server_config.address = "0.0.0.0"
        server_config.port = self.args.port

        self.stream_receiver = receiver.StreamReceiver()
        self.stream_receiver.set_server_config(server_config)

        # VRS is the authoritative raw record of every stream included by the
        # selected profile. JSONL callbacks below provide decoded, analysis-ready data.
        if self.args.record_vrs and hasattr(self.stream_receiver, "record_to_vrs"):
            self.sensors.session_dir.mkdir(parents=True, exist_ok=True)
            self.stream_receiver.record_to_vrs(str(self.sensors.vrs_path))
            print(f"Raw VRS recording: {self.sensors.vrs_path}")

        self.stream_receiver.register_rgb_callback(self.rgb_callback)
        self.stream_receiver.register_audio_callback(self.audio_callback)

        if self.args.enable_sensors:
            for method_name, callback in self.sensors.callbacks().items():
                method = getattr(self.stream_receiver, method_name, None)
                if method is None:
                    self.sensors.mark_unavailable(method_name)
                    print(f"[sensor] unavailable in installed SDK: {method_name}")
                    continue
                try:
                    method(callback)
                    self.sensors.mark_registered(method_name)
                    print(f"[sensor] registered: {method_name}")
                except Exception as exc:
                    self.sensors.mark_unavailable(method_name)
                    print(f"[sensor] could not register {method_name}: {exc}")

        self.stream_receiver.start_server()

        print("[4/4] Waiting for RGB and audio packets...")
        frame_ok = self.state.first_frame_seen.wait(timeout=15)
        audio_ok = self.state.first_audio_seen.wait(timeout=15)
        if not frame_ok:
            print("[WARN] No RGB frame yet. Check profile, port 6768, VPN, and firewall.")
        if not audio_ok:
            print("[WARN] No audio packet yet. Check the selected streaming profile.")
        if frame_ok and audio_ok:
            print("RGB and audio are flowing.")

    def stop(self) -> None:
        """Gracefully stop native streaming, callbacks, VRS, and JSONL logging.

        Native SDK teardown is executed once and from the main thread. The
        deliberate drain delays follow Meta's streaming-example shutdown pattern
        and reduce races between callback processors, VRS writing, and the HTTP
        server on macOS.
        """
        with self._stop_lock:
            if self._stopped:
                return
            self._stopped = True

        self.running = False
        self._stop_requested.set()

        if self.device is not None:
            try:
                stop_tts = getattr(self.device, "stop_tts", None)
                if callable(stop_tts):
                    try:
                        stop_tts()
                    except Exception:
                        pass
                self.device.stop_streaming()
                print("Streaming stopped.")
            except Exception as exc:
                print(f"[WARN] Could not stop device stream cleanly: {exc}")

        # Let packets already in native queues reach callbacks/VRS before the
        # receiver removes callbacks and tears down its processors.
        if self.args.shutdown_drain_seconds > 0:
            time.sleep(self.args.shutdown_drain_seconds)

        if self.stream_receiver is not None:
            clear_callbacks = getattr(self.stream_receiver, "clear_callbacks", None)
            if callable(clear_callbacks):
                try:
                    clear_callbacks()
                    print("Streaming callbacks cleared.")
                    time.sleep(0.25)
                except Exception as exc:
                    print(f"[WARN] Could not clear callbacks explicitly: {exc}")

            stop_server = getattr(self.stream_receiver, "stop_server", None)
            if callable(stop_server):
                try:
                    stop_server()
                    print("Streaming receiver stopped.")
                except Exception as exc:
                    print(f"[WARN] Could not stop receiver cleanly: {exc}")

        # No callback should write after the native receiver has stopped.
        try:
            self.sensors.close(timeout_seconds=self.args.sensor_close_timeout_seconds)
            print("Sensor recorder stopped and manifest finalized.")
        except Exception as exc:
            print(f"[WARN] Could not close sensor recorder cleanly: {exc}")

        self.stream_receiver = None
        self.device = None

    def _start_quit_listener(self) -> None:
        """Allow typing q + Enter to stop wake mode without Ctrl+C."""
        if self._quit_thread is not None and self._quit_thread.is_alive():
            return

        def listen() -> None:
            while self.running and not self._stop_requested.is_set():
                try:
                    command = input().strip().lower()
                except (EOFError, OSError):
                    return
                if command in {"q", "quit", "exit", "stop"}:
                    print("[control] Stop requested. Finishing the current operation...")
                    self.running = False
                    self._stop_requested.set()
                    return

        self._quit_thread = threading.Thread(
            target=listen,
            name="watch-and-tell-quit-listener",
            daemon=True,
        )
        self._quit_thread.start()

    def _interruptible_wait(self, seconds: float) -> bool:
        """Return False when a stop was requested during the wait."""
        return not self._stop_requested.wait(timeout=max(0.0, seconds))

    def _mono_from_multichannel(self, multi: np.ndarray) -> tuple[np.ndarray, int]:
        if multi.ndim != 2 or multi.shape[1] == 0:
            raise ValueError("Invalid multichannel audio shape")

        if self.args.audio_channel != "auto":
            channel = int(self.args.audio_channel)
            if channel < 0 or channel >= multi.shape[1]:
                raise ValueError(
                    f"Audio channel {channel} is invalid; stream has {multi.shape[1]} channels"
                )
        else:
            centered = multi.astype(np.float32) - multi.astype(np.float32).mean(axis=0)
            rms = np.sqrt(np.mean(centered * centered, axis=0) + 1e-9)
            channel = int(np.argmax(rms))

        return multi[:, channel].astype(np.int16, copy=False), channel

    @staticmethod
    def _wav_bytes(mono: np.ndarray) -> bytes:
        output = io.BytesIO()
        with wave.open(output, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(SAMPLE_RATE)
            wav.writeframes(mono.astype("<i2", copy=False).tobytes())
        return output.getvalue()

    @staticmethod
    def _prepare_speech(mono: np.ndarray) -> tuple[np.ndarray, dict[str, float]]:
        """Remove DC, reject silence, trim quiet edges, and normalize clear speech."""
        if mono.size < SAMPLE_RATE // 4:
            raise RuntimeError("The captured audio is too short")

        signal = mono.astype(np.float32)
        signal -= float(np.median(signal))

        frame_len = max(1, int(SAMPLE_RATE * 0.02))
        frame_count = signal.size // frame_len
        if frame_count < 5:
            raise RuntimeError("The captured audio is too short")
        framed = signal[: frame_count * frame_len].reshape(frame_count, frame_len)
        frame_rms = np.sqrt(np.mean(framed * framed, axis=1) + 1e-9)

        noise_rms = float(np.percentile(frame_rms, 20))
        speech_rms = float(np.percentile(frame_rms, 90))
        peak = float(np.percentile(np.abs(signal), 99.5))
        active_threshold = max(noise_rms * 1.8, noise_rms + 20.0, speech_rms * 0.18)
        active = frame_rms >= active_threshold

        min_active_frames = max(3, int(0.12 / 0.02))
        if peak < 35.0 or int(active.sum()) < min_active_frames:
            raise RuntimeError(
                "No clear speech was detected. Speak after the prompt and closer to the glasses."
            )

        active_idx = np.flatnonzero(active)
        pad_frames = int(0.25 / 0.02)
        start_frame = max(0, int(active_idx[0]) - pad_frames)
        end_frame = min(frame_count, int(active_idx[-1]) + pad_frames + 1)
        trimmed = signal[start_frame * frame_len : end_frame * frame_len]

        trimmed_peak = float(np.percentile(np.abs(trimmed), 99.5))
        if trimmed_peak > 0:
            gain = min(12.0, 28000.0 / trimmed_peak)
            trimmed *= gain
        trimmed = np.clip(trimmed, -32768, 32767).astype(np.int16)

        return trimmed, {
            "noise_rms": noise_rms,
            "speech_rms": speech_rms,
            "peak": peak,
            "active_ms": float(active.sum()) * 20.0,
        }

    @staticmethod
    def _looks_like_prompt_leak(text: str) -> bool:
        lowered = re.sub(r"\s+", " ", text.lower()).strip()
        return any(phrase in lowered for phrase in PROMPT_LEAK_PHRASES)

    @staticmethod
    def _wake_match(text: str) -> Optional[re.Match[str]]:
        return WAKE_PATTERN.search(text)

    def transcribe(self, mono: np.ndarray, *, wake_scan: bool = False) -> tuple[str, bytes]:
        prepared, metrics = self._prepare_speech(mono)
        if self.args.audio_debug:
            print(
                "Speech metrics: "
                f"noise_rms={metrics['noise_rms']:.1f}, "
                f"speech_rms={metrics['speech_rms']:.1f}, "
                f"peak={metrics['peak']:.1f}, active_ms={metrics['active_ms']:.0f}"
            )
        wav_bytes = self._wav_bytes(prepared)
        temp_path = ""
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(wav_bytes)
                temp_path = tmp.name
            with open(temp_path, "rb") as fh:
                request: dict[str, Any] = {
                    "model": self.args.transcribe_model,
                    "file": fh,
                    "temperature": 0,
                }
                if self.args.transcription_language:
                    request["language"] = self.args.transcription_language
                # Keep wake scans prompt-free: a literal wake phrase or descriptive
                # prompt can be copied into a transcript when audio is weak.
                if self.args.transcription_prompt and not wake_scan:
                    request["prompt"] = self.args.transcription_prompt
                result = self.client.audio.transcriptions.create(**request)

            text = (result.text or "").strip()
            if wake_scan:
                lowered = re.sub(r"\s+", " ", text.lower()).strip(" .,:;-_")
                if self._looks_like_prompt_leak(text):
                    return "", wav_bytes
                if any(marker in lowered for marker in NO_SPEECH_MARKERS):
                    return "", wav_bytes
            return text, wav_bytes
        finally:
            if temp_path:
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass

    @staticmethod
    def needs_vision(query: str) -> bool:
        q = query.lower().strip()
        return any(hint in q for hint in VISION_HINTS)

    @staticmethod
    def needs_web(query: str) -> bool:
        """Use live search only for clearly time-sensitive/current-information requests."""
        q = query.lower().strip()
        web_hints = (
            "today",
            "latest",
            "current",
            "currently",
            "news",
            "recent",
            "this week",
            "this month",
            "right now",
            "weather",
            "price",
            "stock",
            "score",
            "election",
        )
        return any(hint in q for hint in web_hints)

    def _encode_latest_image(self) -> tuple[Optional[bytes], Optional[int]]:
        frame, timestamp_ns = self.state.get_rgb()
        if frame is None:
            return None, timestamp_ns

        arr = np.asarray(frame)
        if arr.ndim == 3 and arr.shape[0] in (3, 4) and arr.shape[-1] not in (3, 4):
            arr = np.transpose(arr, (1, 2, 0))
        arr = arr.astype(np.uint8, copy=False)
        if arr.ndim == 2:
            image = Image.fromarray(arr).convert("RGB")
        else:
            if arr.shape[-1] == 4:
                arr = arr[..., :3]
            image = Image.fromarray(arr)

        if self.args.rotate_image:
            image = image.rotate(self.args.rotate_image, expand=True)

        image.thumbnail((self.args.max_image_width, self.args.max_image_width))
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=self.args.jpeg_quality, optimize=True)
        return buffer.getvalue(), timestamp_ns

    def _encode_gaze_crop(self, snapshot: dict[str, Any]) -> Optional[bytes]:
        """Create an approximate gaze-centred crop from yaw/pitch.

        This uses configurable RGB field-of-view values and is not a substitute
        for calibration-based projection. The full image is always sent as well.
        """
        latest = snapshot.get("latest", {})
        gaze = latest.get("eye_gaze", {}).get("payload")
        if not gaze:
            return None
        try:
            yaw = float(gaze.get("yaw"))
            pitch = float(gaze.get("pitch"))
        except (TypeError, ValueError):
            return None
        frame, _ = self.state.get_rgb()
        if frame is None:
            return None
        arr = np.asarray(frame)
        if arr.ndim == 3 and arr.shape[0] in (3, 4) and arr.shape[-1] not in (3, 4):
            arr = np.transpose(arr, (1, 2, 0))
        if arr.ndim != 3:
            return None
        if arr.shape[-1] == 4:
            arr = arr[..., :3]
        image = Image.fromarray(arr.astype(np.uint8, copy=False))
        if self.args.rotate_image:
            image = image.rotate(self.args.rotate_image, expand=True)
        w, h = image.size
        hfov = np.deg2rad(self.args.rgb_hfov_degrees)
        vfov = np.deg2rad(self.args.rgb_vfov_degrees)
        cx = int(np.clip((0.5 + yaw / hfov) * w, 0, w - 1))
        cy = int(np.clip((0.5 + pitch / vfov) * h, 0, h - 1))
        size = int(max(128, min(w, h) * self.args.gaze_crop_fraction))
        left = max(0, min(w - size, cx - size // 2))
        top = max(0, min(h - size, cy - size // 2))
        crop = image.crop((left, top, left + size, top + size))
        crop.thumbnail((self.args.max_image_width, self.args.max_image_width))
        buffer = io.BytesIO()
        crop.save(buffer, format="JPEG", quality=self.args.jpeg_quality, optimize=True)
        return buffer.getvalue()

    @staticmethod
    def _extract_sources(response_dict: dict[str, Any]) -> list[dict[str, str]]:
        sources: list[dict[str, str]] = []
        seen: set[str] = set()

        def walk(value: Any) -> None:
            if isinstance(value, dict):
                url = value.get("url")
                if isinstance(url, str) and url.startswith("http") and url not in seen:
                    seen.add(url)
                    sources.append(
                        {
                            "title": str(value.get("title") or ""),
                            "url": url,
                        }
                    )
                for child in value.values():
                    walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)

        walk(response_dict)
        return sources

    def ask_openai(
        self,
        query: str,
        image_bytes: Optional[bytes],
        gaze_crop_bytes: Optional[bytes] = None,
        sensor_context: str = "",
    ) -> tuple[str, str, list[dict[str, str]]]:
        model_text = query
        if sensor_context:
            model_text += "\n\nLive sensor context (research measurements; use cautiously):\n" + sensor_context
        content: list[dict[str, Any]] = [{"type": "input_text", "text": model_text}]
        if image_bytes is not None:
            encoded = base64.b64encode(image_bytes).decode("ascii")
            content.append(
                {
                    "type": "input_image",
                    "image_url": f"data:image/jpeg;base64,{encoded}",
                    "detail": "low",
                }
            )
        if gaze_crop_bytes is not None:
            gaze_encoded = base64.b64encode(gaze_crop_bytes).decode("ascii")
            content.append(
                {
                    "type": "input_image",
                    "image_url": f"data:image/jpeg;base64,{gaze_encoded}",
                    "detail": "high",
                }
            )

        request: dict[str, Any] = {
            "model": self.args.model,
            "instructions": (
                "You are Watch and Tell, an assistant for a wearer of Meta Aria Gen 2 research glasses. "
                "Answer clearly and accurately. For scene questions, use the full wearer-view image; "
                "when a second image is present, it is an approximate gaze-centred crop. "
                "For pointing questions, combine the image with hand-tracking context, but state uncertainty. "
                "Sensor and PPG values are research signals, not medical measurements. "
                "Do not identify private people or infer sensitive personal traits. "
                "Keep the spoken answer under 60 words unless the user explicitly requests detail. "
                "When uncertain, say so."
            ),
            "input": [{"role": "user", "content": content}],
        }
        if self.needs_web(query):
            request["tools"] = [{"type": "web_search"}]

        response = self.client.responses.create(**request)
        answer = (response.output_text or "I could not produce an answer.").strip()
        response_dict = response.model_dump()
        response_json = json.dumps(response_dict, ensure_ascii=False, indent=2, default=str)
        sources = self._extract_sources(response_dict)
        return answer, response_json, sources

    def speak(self, text: str) -> None:
        if self.device is None:
            print("[WARN] Device is not connected; cannot speak through glasses.")
            return
        spoken = re.sub(r"https?://\S+", "", text).strip()
        if not spoken:
            return
        self.device.render_tts(text=spoken)
        word_count = max(1, len(spoken.split()))
        estimated = min(15.0, max(2.0, word_count / 2.4 + 1.0))
        self.speaking_until = time.time() + estimated

    def handle_query(self, query: str, wav_bytes: bytes, mode: str) -> None:
        query = query.strip(" ,.:;-")
        if not query:
            return

        record_id = str(uuid.uuid4())
        now_local = datetime.now().astimezone()
        now_utc = datetime.now(timezone.utc)
        vision = self.needs_vision(query)
        image_bytes: Optional[bytes] = None
        image_path = ""
        audio_path = self.logger.save_audio(wav_bytes, record_id)
        response_path = ""
        response_json = ""
        sensor_snapshot = self.sensors.snapshot(self.args.sensor_snapshot_window_seconds)
        sensor_snapshot_path = self.sensors.save_snapshot(sensor_snapshot, record_id)
        sensor_context = self.sensors.model_context(sensor_snapshot) if self.args.use_sensor_context else ""
        gaze_crop_bytes: Optional[bytes] = None
        sources: list[dict[str, str]] = []
        answer = ""
        status = "success"
        error = ""
        start = time.perf_counter()

        try:
            if vision or self.args.save_image_every_query:
                image_bytes, _ = self._encode_latest_image()
                if vision and image_bytes is None:
                    raise RuntimeError("No recent RGB frame is available")
                if image_bytes is not None:
                    image_path = self.logger.save_image(image_bytes, record_id)
                if self.args.gaze_guided_vision:
                    gaze_crop_bytes = self._encode_gaze_crop(sensor_snapshot)

            print(f"Question: {query}")
            if sensor_context:
                print(f"Sensor context: {sensor_context}")
            answer, response_json, sources = self.ask_openai(
                query=query,
                image_bytes=image_bytes if vision else None,
                gaze_crop_bytes=gaze_crop_bytes if vision else None,
                sensor_context=sensor_context,
            )
            response_path = self.logger.save_response(response_json, record_id)
            print(f"Answer: {answer}")
            if sources:
                print("Sources:")
                for source in sources[:5]:
                    print(f"  - {source.get('title') or source.get('url')}: {source.get('url')}")
            self.speak(answer)
        except Exception as exc:
            status = "error"
            error = str(exc)
            answer = f"Sorry, I could not answer that. {exc}"
            print(answer)
            try:
                self.speak("Sorry, I could not answer that question.")
            except Exception:
                pass

        latency_ms = int((time.perf_counter() - start) * 1000)
        self.logger.append_row(
            {
                "record_id": record_id,
                "timestamp_local": now_local.isoformat(),
                "timestamp_utc": now_utc.isoformat(),
                "query": query,
                "mode": mode,
                "vision_used": vision,
                "image_path": image_path,
                "audio_path": audio_path,
                "answer": answer,
                "model": self.args.model,
                "latency_ms": latency_ms,
                "status": status,
                "error": error,
                "sources": sources,
                "response_json_path": response_path,
                "sensor_snapshot_path": sensor_snapshot_path,
                "sensor_context": sensor_context,
            }
        )

    def capture_question(self, seconds: float) -> tuple[str, bytes]:
        self.state.audio.clear()
        print(f"Speak now for up to {seconds:.1f} seconds...")
        time.sleep(seconds)
        multi = self.state.audio.snapshot(seconds)
        if multi is None or len(multi) < SAMPLE_RATE // 2:
            raise RuntimeError("Not enough audio was captured")
        mono, channel = self._mono_from_multichannel(multi)
        print(f"Using audio channel {channel} of {multi.shape[1]}")
        return self.transcribe(mono)

    def run_keyboard_mode(self) -> None:
        print("\nKeyboard mode is ready.")
        print("Press Enter, speak your question, and wait for the answer. Type q then Enter to quit.")
        while self.running:
            command = input("\nEnter to ask (q to quit): ").strip().lower()
            if command == "q":
                break
            try:
                transcript, wav_bytes = self.capture_question(self.args.listen_seconds)
                print(f"Transcript: {transcript}")
                cleaned = WAKE_PATTERN.sub("", transcript, count=1).strip(" ,.:;-")
                self.handle_query(cleaned or transcript, wav_bytes, mode="keyboard")
                while time.time() < self.speaking_until:
                    time.sleep(0.2)
                self.state.audio.clear()
            except Exception as exc:
                print(f"[ERROR] {exc}")

    @staticmethod
    def _rms_for_channel(multi: np.ndarray, channel: int) -> float:
        if multi.ndim != 2 or channel < 0 or channel >= multi.shape[1]:
            raise ValueError(
                f"Wake VAD channel {channel} is invalid for shape {multi.shape}"
            )
        signal = multi[:, channel].astype(np.float32)
        signal -= float(np.mean(signal))
        return float(np.sqrt(np.mean(signal * signal) + 1e-9))

    def run_wake_mode(self) -> None:
        print("\nWake-word mode is ready. Say: 'Hey Meta, what am I looking at?' or a general question.")
        print(
            "The calibrated wearer-speech channel is used for local speech-activity "
            "gating and transcription."
        )
        print("Type q then Enter to stop cleanly; Ctrl+C is also supported.")
        self._start_quit_listener()

        wake_vad_channel = int(self.args.wake_vad_channel)
        last_text = ""
        cooldown_until = 0.0
        self.state.audio.clear()

        print(
            f"Remain quiet for {self.args.wake_vad_calibration_seconds:.1f} seconds "
            f"while wake VAD channel {wake_vad_channel} is calibrated..."
        )
        if not self._interruptible_wait(self.args.wake_vad_calibration_seconds):
            return
        calibration = self.state.audio.snapshot(self.args.wake_vad_calibration_seconds)
        if calibration is None:
            raise RuntimeError("No audio was available for wake VAD calibration")
        baseline_rms = self._rms_for_channel(calibration, wake_vad_channel)
        # Use both a relative and additive margin. A 3x multiplier was too high
        # for wearer speech and could make the wake trigger unreachable.
        threshold = max(
            self.args.wake_rms_threshold,
            baseline_rms * self.args.wake_vad_multiplier,
            baseline_rms + self.args.wake_vad_margin,
        )
        print(
            f"Wake VAD calibrated: channel={wake_vad_channel}, "
            f"baseline_rms={baseline_rms:.1f}, threshold={threshold:.1f}"
        )
        self.state.audio.clear()

        last_debug_print = 0.0

        while self.running and not self._stop_requested.is_set():
            if not self._interruptible_wait(self.args.wake_hop_seconds):
                break
            if time.time() < max(cooldown_until, self.speaking_until):
                continue

            vad_multi = self.state.audio.snapshot(self.args.wake_vad_window_seconds)
            if vad_multi is None or len(vad_multi) < int(SAMPLE_RATE * 0.15):
                continue

            try:
                vad_rms = self._rms_for_channel(vad_multi, wake_vad_channel)

                # Slowly track changing room noise only while below the current trigger.
                if vad_rms < threshold * 0.85:
                    baseline_rms = 0.995 * baseline_rms + 0.005 * vad_rms
                    threshold = max(
                        self.args.wake_rms_threshold,
                        baseline_rms * self.args.wake_vad_multiplier,
                        baseline_rms + self.args.wake_vad_margin,
                    )

                now = time.time()
                if self.args.wake_debug and now - last_debug_print >= 1.0:
                    print(
                        f"[wake-vad] channel={wake_vad_channel}, "
                        f"rms={vad_rms:.1f}, threshold={threshold:.1f}"
                    )
                    last_debug_print = now

                if vad_rms < threshold:
                    continue

                print(
                    f"[wake-vad] Speech activity detected on channel {wake_vad_channel}; "
                    f"capturing {self.args.wake_window_seconds:.1f} seconds..."
                )

                # Preserve the speech onset already present in the VAD window.
                # Waiting a full wake window here would push "Hey Meta" out of the
                # subsequent snapshot and make valid requests fail wake matching.
                remaining = max(
                    0.25,
                    self.args.wake_window_seconds - self.args.wake_vad_window_seconds,
                )
                if not self._interruptible_wait(remaining):
                    break
                multi = self.state.audio.snapshot(self.args.wake_window_seconds)
                if multi is None or len(multi) < SAMPLE_RATE:
                    cooldown_until = time.time() + 1.0
                    continue

                mono, channel = self._mono_from_multichannel(multi)
                transcript, wav_bytes = self.transcribe(mono, wake_scan=True)
                normalized = re.sub(r"\s+", " ", transcript.lower()).strip()
                if not normalized or normalized == last_text:
                    cooldown_until = time.time() + 1.0
                    continue
                last_text = normalized

                match = self._wake_match(transcript)
                if not match:
                    if self.args.wake_debug:
                        print(f"[wake] Ignored non-wake speech: {transcript}")
                    cooldown_until = time.time() + 1.0
                    self.state.audio.clear()
                    continue

                print(f"Heard: {transcript}")
                query = transcript[match.end() :].strip(" ,.:;-")

                if len(query.split()) < 2:
                    print("Wake phrase detected. Ask your question now.")
                    self.state.audio.clear()
                    transcript2, wav_bytes2 = self.capture_question(self.args.listen_seconds)
                    print(f"Follow-up transcript: {transcript2}")
                    query = WAKE_PATTERN.sub("", transcript2, count=1).strip(" ,.:;-")
                    wav_bytes = wav_bytes2

                if not query or self._looks_like_prompt_leak(query):
                    print("[wake] Ignoring empty or implausible follow-up transcript.")
                    self.state.audio.clear()
                    cooldown_until = time.time() + 2.0
                    continue

                self.handle_query(query, wav_bytes, mode="wake")
                last_text = ""
                cooldown_until = max(self.speaking_until + 1.5, time.time() + 5.0)
                self.state.audio.clear()
            except Exception as exc:
                print(f"[WARN] Wake loop error: {exc}")
                cooldown_until = time.time() + 1.0

    def run(self) -> None:
        self.connect_and_stream()
        print(f"User ID: {self.user_id}")
        print(f"Audio channel: {self.args.audio_channel}")
        if self.args.mode == "wake":
            print(f"Wake VAD channel: {self.args.wake_vad_channel}")
        print(f"Transcription language: {self.args.transcription_language or 'auto'}")
        print(f"Sensors enabled: {self.args.enable_sensors}")
        print(f"Decoded sensor logging: {self.args.save_sensors}")
        print(f"Raw VRS recording: {self.args.record_vrs}")
        if self.args.save_sensors:
            print(f"Sensor session directory: {self.sensors.session_dir}")
        print(f"Data logging: {'ON' if self.logger.enabled else 'OFF'}")
        if self.logger.enabled:
            print(f"Data directory: {self.logger.base_dir}")

        if self.args.mode == "keyboard":
            self.run_keyboard_mode()
        else:
            self.run_wake_mode()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Watch and Tell prototype for Meta Aria Gen 2 + OpenAI"
    )
    parser.add_argument("--serial", default="", help="Optional Aria Gen 2 serial number")
    parser.add_argument("--profile", default="profile9", help="Aria streaming profile")
    parser.add_argument("--port", type=int, default=6768, help="Streaming receiver port")
    parser.add_argument("--mode", choices=("keyboard", "wake"), default="keyboard")
    parser.add_argument("--listen-seconds", type=float, default=6.0)
    parser.add_argument("--wake-window-seconds", type=float, default=4.0)
    parser.add_argument("--wake-hop-seconds", type=float, default=0.25)
    parser.add_argument(
        "--wake-rms-threshold",
        type=float,
        default=25.0,
        help="Minimum signed-PCM RMS threshold used for wake VAD.",
    )
    parser.add_argument(
        "--wake-vad-channel",
        default="7",
        help="Microphone channel used for local speech-activity gating; channel 7 is calibrated for wearer speech.",
    )
    parser.add_argument("--wake-vad-window-seconds", type=float, default=0.5)
    parser.add_argument("--wake-vad-calibration-seconds", type=float, default=3.0)
    parser.add_argument("--wake-vad-multiplier", type=float, default=2.0)
    parser.add_argument("--wake-vad-margin", type=float, default=10.0)
    parser.add_argument("--wake-debug", action="store_true", help="Print wake VAD diagnostics")
    parser.add_argument("--audio-debug", action="store_true", help="Print PCM conversion and speech metrics")
    parser.add_argument(
        "--transcription-language",
        default=os.getenv("OPENAI_TRANSCRIPTION_LANGUAGE", "en"),
        help="ISO-639-1 language code such as 'en'; use an empty string for auto-detection.",
    )
    parser.add_argument(
        "--transcription-prompt",
        default=os.getenv("OPENAI_TRANSCRIPTION_PROMPT", ""),
        help="Optional neutral transcription context. Do not include the wake phrase.",
    )
    parser.add_argument(
        "--audio-channel",
        default="7",
        help="0-based channel index or 'auto'. Channel 7 is calibrated for wearer speech on this device.",
    )
    parser.add_argument("--rotate-image", type=int, default=0, choices=(0, 90, 180, 270))
    parser.add_argument("--max-image-width", type=int, default=1280)
    parser.add_argument("--jpeg-quality", type=int, default=85)
    parser.add_argument("--save-data", action="store_true", help="Save CSV, audio, images, and raw response JSON")
    parser.add_argument("--enable-sensors", action=argparse.BooleanOptionalAction, default=True, help="Register every sensor callback available in the installed SDK")
    parser.add_argument("--save-sensors", action=argparse.BooleanOptionalAction, default=True, help="Continuously save decoded sensor callbacks to JSONL and per-query snapshots")
    parser.add_argument("--record-vrs", action=argparse.BooleanOptionalAction, default=True, help="Record the complete streamed session to VRS")
    parser.add_argument("--use-sensor-context", action=argparse.BooleanOptionalAction, default=True, help="Include a concise sensor summary in model requests")
    parser.add_argument("--gaze-guided-vision", action=argparse.BooleanOptionalAction, default=True, help="Add an approximate gaze-centred crop for visual questions")
    parser.add_argument("--sensor-rolling-seconds", type=float, default=45.0)
    parser.add_argument("--sensor-snapshot-window-seconds", type=float, default=10.0)
    parser.add_argument("--sensor-manifest-interval-seconds", type=float, default=5.0)
    parser.add_argument("--sensor-close-timeout-seconds", type=float, default=20.0)
    parser.add_argument("--shutdown-drain-seconds", type=float, default=2.0)
    parser.add_argument("--ppg-window-seconds", type=float, default=30.0)
    parser.add_argument("--ppg-min-duration-seconds", type=float, default=30.0)
    parser.add_argument("--ppg-default-sample-rate", type=float, default=128.0)
    parser.add_argument("--ppg-motion-gyro-threshold", type=float, default=0.35)
    parser.add_argument("--ppg-peak-ratio-threshold", type=float, default=4.0)
    parser.add_argument("--rgb-hfov-degrees", type=float, default=110.0, help="Approximate RGB horizontal FOV used only for gaze crop")
    parser.add_argument("--rgb-vfov-degrees", type=float, default=90.0, help="Approximate RGB vertical FOV used only for gaze crop")
    parser.add_argument("--gaze-crop-fraction", type=float, default=0.35)
    parser.add_argument("--save-image-every-query", action="store_true")
    parser.add_argument("--data-dir", default="./data")
    parser.add_argument("--user-id", default="")
    parser.add_argument("--model", default=os.getenv("OPENAI_MODEL", "gpt-5.6"))
    parser.add_argument(
        "--transcribe-model",
        default=os.getenv("OPENAI_TRANSCRIBE_MODEL", "gpt-4o-transcribe"),
    )
    return parser.parse_args()


def main() -> int:
    load_dotenv(dotenv_path=ENV_FILE, override=True)
    args = parse_args()

    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY is missing. Put it in .env or export it in the shell.")
        return 2

    app = WatchAndTellApp(args)

    def handle_signal(signum: int, frame: Any) -> None:
        del signum, frame
        print("\nStopping...")
        app.stop()

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    try:
        app.run()
    except KeyboardInterrupt:
        pass
    except Exception as exc:
        print(f"[FATAL] {exc}")
        return 1
    finally:
        app.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
