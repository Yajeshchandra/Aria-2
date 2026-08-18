"""V6 — silent, QR-synced Aria Gen 2 recorder for the moral-choice study.

Not a voice assistant. Connects to Aria Gen 2, records the full sensor
suite (VRS + decoded JSONL, unchanged from V5.1), and additionally scans
the RGB stream for QR codes shown on the presentation tool's scene/question
pages, logging each detection as a timestamped event on the sensor
recorder's own clock. See design/HLD.md and design/LLD.md for the full
system design and QR payload schema. What changed and why is in
HISTORY.md and ROADMAP.md Goal 1.

Superseded from V5.1: wake-word detection, the OpenAI Q&A loop,
text-to-speech, and all audio-question capture. No voice channel exists
in the current study design (HISTORY.md, 2026-08-17). Microphone streams
still flow into VRS as part of the full sensor suite; nothing in this
file processes them.
"""

from __future__ import annotations

import argparse
import os
import signal
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import numpy as np
from dotenv import load_dotenv
from PIL import Image
from pyzbar.pyzbar import decode as decode_qr_codes

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


class SharedState:
    """Latest RGB frame, kept for QR scanning. No audio buffering — see module docstring."""

    def __init__(self) -> None:
        self._frame_lock = threading.Lock()
        self._latest_rgb: Optional[np.ndarray] = None
        self._latest_rgb_timestamp_ns: Optional[int] = None
        self.first_frame_seen = threading.Event()
        self.first_audio_seen = threading.Event()

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


class StudyRecorderApp:
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.state = SharedState()
        self.device_client: Optional[Any] = None
        self.device: Optional[Any] = None
        self.stream_receiver: Optional[Any] = None
        self.running = True
        self._stopped = False
        self._stop_lock = threading.Lock()
        self._stop_requested = threading.Event()
        self._quit_thread: Optional[threading.Thread] = None
        self._last_qr_payload: Optional[str] = None

        data_dir = Path(os.getenv("WATCH_DATA_DIR", args.data_dir))
        self.user_id = self._require_user_id(args)
        self.sensors = SensorRecorder(
            base_dir=data_dir,
            user_id=self.user_id,
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
    def _require_user_id(args: argparse.Namespace) -> str:
        user_id = args.user_id or os.getenv("WATCH_USER_ID")
        if not user_id:
            raise SystemExit(
                "A participant/session ID is required for study recording: pass --user-id "
                "or set WATCH_USER_ID. Refusing to invent one, since a study session must "
                "be attributable to a known participant."
            )
        return user_id

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
        # Presence check only. VRS records the raw audio stream at the
        # native SDK level regardless of Python callback registration; this
        # callback exists purely so startup can confirm audio is flowing.
        del audio_data, audio_record, num_channels
        self.state.first_audio_seen.set()

    def connect_and_stream(self) -> None:
        print("[1/4] Connecting to Aria Gen 2...")
        self.device_client = sdk_gen2.DeviceClient()
        config = sdk_gen2.DeviceClientConfig()
        legacy_serial_config = bool(
            self.args.serial and hasattr(config, "device_serial")
        )
        if legacy_serial_config:
            config.device_serial = self.args.serial
        if self.args.ip_address:
            # DeviceClient connects over USB by default. Under WSL2 (no
            # native USB passthrough without usbipd-win) or any headless
            # capture box, connect over Wi-Fi instead by supplying the
            # glasses' IP -- get it from the Mobile Companion App:
            # Dashboard -> tap Wi-Fi.
            config.ip_v4_address = self.args.ip_address
            print(f"Connecting over Wi-Fi to {self.args.ip_address}")
        self.device_client.set_client_config(config)

        if self.args.serial and not legacy_serial_config and hasattr(sdk_gen2, "DeviceTarget"):
            target = sdk_gen2.DeviceTarget(serial=self.args.serial)
            self.device = self.device_client.connect(target)
        else:
            self.device = self.device_client.connect()
        print(f"Connected: {self.device.connection_id()}")

        print(f"[2/4] Starting stream with profile: {self.args.profile}")
        streaming_config = sdk_gen2.StreamingConfig()
        streaming_config.profile_name = self.args.profile
        # Default interface is USB (confirmed via `aria_gen2 streaming start --help`).
        # Under WSL2 -- no USB passthrough -- streaming silently tried and failed over
        # USB even though the control/pairing connection was over Wi-Fi. Force station
        # mode explicitly (device joins the existing Wi-Fi network, same as this host).
        streaming_config.streaming_interface = sdk_gen2.StreamingInterface.WifiStation
        self.device.set_streaming_config(streaming_config)
        self.device.start_streaming()

        print(f"[3/4] Starting receiver on 0.0.0.0:{self.args.port}")
        server_config = sdk_gen2.ServerConfig()  # renamed from HttpServerConfig -- unverified, check if this errors
        server_config.address = "0.0.0.0"
        server_config.port = self.args.port

        self.stream_receiver = receiver.StreamReceiver()
        self.stream_receiver.set_server_config(server_config)

        # VRS is the authoritative raw record of every stream included by the
        # selected profile, independent of which Python callbacks below are
        # registered. JSONL callbacks provide decoded, analysis-ready data.
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
        """Gracefully stop native streaming, callbacks, VRS, and JSONL logging."""
        with self._stop_lock:
            if self._stopped:
                return
            self._stopped = True

        self.running = False
        self._stop_requested.set()

        if self.device is not None:
            try:
                self.device.stop_streaming()
                print("Streaming stopped.")
            except Exception as exc:
                print(f"[WARN] Could not stop device stream cleanly: {exc}")

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

        try:
            self.sensors.close(timeout_seconds=self.args.sensor_close_timeout_seconds)
            print("Sensor recorder stopped and manifest finalized.")
        except Exception as exc:
            print(f"[WARN] Could not close sensor recorder cleanly: {exc}")

        self.stream_receiver = None
        self.device = None

    def _start_quit_listener(self) -> None:
        """Allow typing q + Enter to stop recording without Ctrl+C."""
        if self._quit_thread is not None and self._quit_thread.is_alive():
            return

        def listen() -> None:
            while self.running and not self._stop_requested.is_set():
                try:
                    command = input().strip().lower()
                except (EOFError, OSError):
                    return
                if command in {"q", "quit", "exit", "stop"}:
                    print("[control] Stop requested. Finishing cleanly...")
                    self.running = False
                    self._stop_requested.set()
                    return

        self._quit_thread = threading.Thread(
            target=listen,
            name="study-recorder-quit-listener",
            daemon=True,
        )
        self._quit_thread.start()

    def _interruptible_wait(self, seconds: float) -> bool:
        """Return False when a stop was requested during the wait."""
        return not self._stop_requested.wait(timeout=max(0.0, seconds))

    def _scan_for_qr(self) -> tuple[Optional[str], Optional[int]]:
        """Decode any QR code visible in the latest RGB frame.

        Returns (payload, frame_timestamp_ns). Payload format is
        "<page_type>:<id>" per design/LLD.md §2. Returns (None, None) when
        no frame is available yet or no code is currently visible.
        """
        frame, timestamp_ns = self.state.get_rgb()
        if frame is None:
            return None, None

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

        results = decode_qr_codes(image)
        if not results:
            return None, timestamp_ns
        payload = results[0].data.decode("utf-8", errors="replace")
        return payload, timestamp_ns

    def run_record_mode(self) -> None:
        print("\nRecording is live. Show a scene/question QR code to the glasses to log a sync event.")
        print("Type q then Enter to stop cleanly; Ctrl+C is also supported.")
        self._start_quit_listener()

        while self.running and not self._stop_requested.is_set():
            if not self._interruptible_wait(self.args.qr_scan_interval_seconds):
                break
            try:
                payload, timestamp_ns = self._scan_for_qr()
            except Exception as exc:
                print(f"[WARN] QR scan error: {exc}")
                continue
            if payload is None or payload == self._last_qr_payload:
                continue
            self._last_qr_payload = payload
            self.sensors.record("events", {"event": "qr_detected", "qr_payload": payload}, timestamp_ns)
            stamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{stamp}] QR detected: {payload}")

    def run(self) -> None:
        self.connect_and_stream()
        print(f"User ID: {self.user_id}")
        print(f"Sensors enabled: {self.args.enable_sensors}")
        print(f"Decoded sensor logging: {self.args.save_sensors}")
        print(f"Raw VRS recording: {self.args.record_vrs}")
        if self.args.save_sensors:
            print(f"Sensor session directory: {self.sensors.session_dir}")

        self.run_record_mode()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="V6 silent recorder for Meta Aria Gen 2 — moral-choice study"
    )
    parser.add_argument("--serial", default="", help="Optional Aria Gen 2 serial number (USB connections)")
    parser.add_argument(
        "--ip-address",
        default=os.getenv("ARIA_IP_ADDRESS", ""),
        help="Glasses' IP address for Wi-Fi connection (Mobile Companion App -> Dashboard -> Wi-Fi). "
        "Required under WSL2 -- no native USB passthrough. Falls back to USB when omitted.",
    )
    parser.add_argument("--profile", default="profile9", help="Aria streaming profile")
    parser.add_argument("--port", type=int, default=6768, help="Streaming receiver port")
    parser.add_argument("--rotate-image", type=int, default=0, choices=(0, 90, 180, 270))
    parser.add_argument(
        "--qr-scan-interval-seconds",
        type=float,
        default=0.5,
        help="How often to scan the latest RGB frame for a QR code",
    )
    parser.add_argument("--enable-sensors", action=argparse.BooleanOptionalAction, default=True, help="Register every sensor callback available in the installed SDK")
    parser.add_argument("--save-sensors", action=argparse.BooleanOptionalAction, default=True, help="Continuously save decoded sensor callbacks to JSONL")
    parser.add_argument("--record-vrs", action=argparse.BooleanOptionalAction, default=True, help="Record the complete streamed session to VRS")
    parser.add_argument("--sensor-rolling-seconds", type=float, default=45.0)
    parser.add_argument("--sensor-manifest-interval-seconds", type=float, default=5.0)
    parser.add_argument("--sensor-close-timeout-seconds", type=float, default=20.0)
    parser.add_argument("--shutdown-drain-seconds", type=float, default=2.0)
    parser.add_argument("--ppg-window-seconds", type=float, default=30.0)
    parser.add_argument("--ppg-min-duration-seconds", type=float, default=30.0)
    parser.add_argument("--ppg-default-sample-rate", type=float, default=128.0)
    parser.add_argument("--ppg-motion-gyro-threshold", type=float, default=0.35)
    parser.add_argument("--ppg-peak-ratio-threshold", type=float, default=4.0)
    parser.add_argument("--data-dir", default="./data")
    parser.add_argument("--user-id", default="", help="Participant/session ID. Required (or set WATCH_USER_ID).")
    return parser.parse_args()


def main() -> int:
    load_dotenv(dotenv_path=ENV_FILE, override=True)
    args = parse_args()
    app = StudyRecorderApp(args)

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
