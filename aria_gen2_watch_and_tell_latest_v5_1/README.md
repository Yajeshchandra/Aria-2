# V6 — Meta Aria Gen 2 study recorder

Silent, QR-synced recorder for the moral-choice study. Not a voice assistant — V5.1's wake-word detection, OpenAI Q&A loop, and text-to-speech are gone. See `../HISTORY.md` (2026-08-17) for why, and `../design/HLD.md` / `../design/LLD.md` for how this fits the rest of the system.

## What is recorded

- Complete streamed session in VRS — the authoritative raw record.
- Continuous decoded JSONL for every sensor callback available in the installed SDK and selected profile: dual IMUs, eye gaze, VIO, barometer, magnetometer, GPS, phone location, PPG, Bluetooth/Wi-Fi beacons, device calibration.
- A continuous `events` JSONL stream: one entry per detected QR code, giving the ground-truth timestamp for every scene/question page shown on the separate presentation tool. See `../design/LLD.md` §2–3 for the payload format.

Not recorded at the app level: no per-question audio/image artifacts, no interaction CSV — there are no questions anymore. Microphone audio still flows into VRS as part of the full sensor suite; nothing in this codebase processes it. Hand pose and high-frequency VIO are not registered — both existed only to support the old pointing/holding voice queries and feed nothing in the current feature plan.

A registered callback can still have zero samples when the selected profile or environment does not deliver that stream.

## Two clocks, used for different things

Every sensor event carries a device-reported `timestamp_ns` (may be boot-relative, not Unix-epoch, depending on the SDK build) and a host-reported `received_ns` (this machine's wall clock at the moment the event was recorded). Cross-stream windowing (snapshot cutoffs, QR-to-sensor alignment) uses `received_ns` exclusively, since comparing device timestamps across streams on different epochs was a real, confirmed bug. Precise within-stream timing (PPG sample-rate inference) still uses the device `timestamp_ns`, where host-side jitter would be the wrong thing to measure. `test_v5_1.py::test_mixed_clock_origin_windowing` exercises the exact scenario this fixes.

## QR-based scene/question sync

The recorder scans the latest RGB frame for a QR code every `--qr-scan-interval-seconds` (default 0.5s). A new code (different from the last one seen) is logged as an `events` entry with the RGB frame's own device timestamp. The presentation tool's own response log records *what* was chosen; this stream records *when* each page was shown — see `design/HLD.md` §2.3 for why neither can do the other's job.

Generate the QR codes for a set of pages:

```bash
python generate_qr.py pages.csv --out-dir qr_codes
```

where `pages.csv` has columns `page_type,id` (e.g. `scene,story_03_scene_2`).

## PPG research estimate

Unchanged from V5.1. PPG is continuously recorded. A pulse estimate is attempted only when:

- at least 30 seconds of PPG are available;
- the signal is non-flat;
- head-motion RMS is below the configured threshold;
- the dominant spectral peak is within 42–180 bpm; and
- spectral peak confidence exceeds the configured threshold.

Explicitly research-only, not a medical measurement. Rejected estimates retain a status such as `need_longer_window`, `rejected_due_to_motion`, or `low_spectral_confidence`.

## Audio conversion note (historical)

V4/V5.1 fixed a Q16 fixed-point audio decoding bug in a now-removed `AudioRingBuffer` class — the SDK reported `int64` values like `-1114112` (`= -17 * 65536`), signed PCM with 16 shift bits, which a naive clip would have silently corrupted into a fake carrier signal. That code is gone because nothing in V6 processes live audio anymore (VRS captures it untouched). If audio processing is ever added back — e.g. a spoken end-of-session reflection — re-read this note before touching PCM conversion; the SDK-level dtype quirk is a hardware/SDK behavior, not specific to the deleted code.

## Setup

Requires macOS or Linux. The Project Aria Client SDK supports Mac Big Sur+, Fedora 36+ and Ubuntu 22.04+ on Python 3.10–3.12; there is no Windows build. `pyzbar` additionally needs the system `zbar` library (`brew install zbar` on macOS).

```bash
conda activate MetaAriaGlasses
cd /path/to/aria_gen2_watch_and_tell_latest_v5_1
cp .env.example .env     # set WATCH_USER_ID / WATCH_DATA_DIR if not passing --user-id
python -m pip install -r requirements.txt
./check_setup.sh
```

`check_setup.sh` byte-compiles every module and runs the test suite, so no separate compile step is needed.

## Run

```bash
./run_record.sh P001
```

or set `WATCH_USER_ID` in `.env` and run without an argument. A participant/session ID is required — the recorder refuses to invent one, since a study session must be attributable to a known participant.

Type `q` then Enter to stop cleanly; `Ctrl+C` is also supported.

## Output layout

```text
data/
└── sensors/
    └── P001_YYYYMMDD_HHMMSS/
        ├── manifest.json
        ├── P001_..._all_streams.vrs/
        │   └── ...timestamp....vrs
        └── streams/
            ├── imu_imu-left.jsonl
            ├── imu_imu-right.jsonl
            ├── eye_gaze.jsonl
            ├── vio.jsonl
            ├── ppg.jsonl
            ├── events.jsonl        ← QR detections, see design/LLD.md §3
            └── ...
```

## Inspect the latest session

```bash
python inspect_sensor_session.py
```

Inspect a specific session:

```bash
python inspect_sensor_session.py data/sensors/P001_YYYYMMDD_HHMMSS
```

## Study-use checklist

Before formal participant recording, verify:

- `closed_cleanly: true` in `manifest.json`;
- non-zero counts for every required stream, including `events`;
- `dropped_jsonl_events` is empty or understood;
- the VRS file exists and has a plausible size;
- a real QR round-trip on the actual presentation tool, not just the synthetic test — confirm the recorder logs an event when a real page is shown;
- PPG estimates are retained as research-only values with quality status.
