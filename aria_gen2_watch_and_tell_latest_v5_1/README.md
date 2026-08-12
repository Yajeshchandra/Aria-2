# Watch and Tell V5.1 — Meta Aria Gen 2 multimodal recorder

V5.1 is the reliability update to V5. It preserves the validated Aria audio, RGB, wake-word, sensor, VRS, and OpenAI pipeline while correcting shutdown, pointing-query routing, wake-phrase variants, sensor-prompt length, manifest finalization, and PPG quality screening.

## What is recorded

- Complete streamed session in VRS.
- RGB images used for visual questions.
- Channel-7 wearer-speech WAV files and transcripts.
- OpenAI response JSON and interaction CSV.
- Continuous decoded JSONL for every callback available in the installed SDK and selected profile: dual IMUs, eye gaze, hand pose, VIO, high-frequency VIO, barometer, magnetometer, GPS, phone location, PPG, Bluetooth/Wi-Fi beacons, and device calibration.
- Per-question sensor snapshot JSON with latest values, session counts, dropped-event counts, and rolling summaries.

VRS remains the authoritative raw record. JSONL is the analysis-ready decoded record. A registered callback can still have zero samples when the selected profile or environment does not deliver that stream.

## V5.1 improvements

### Clean shutdown and metadata integrity

The application stops device streaming, waits for native queues to drain, clears callbacks when the SDK exposes that method, stops the receiver, drains the JSONL queue, and finalizes the manifest. The manifest is also checkpointed every five seconds, so counts are retained even after an unexpected process failure.

In wake mode, type:

```text
q
```

and press Enter for a clean stop. `Ctrl+C` remains supported.

### Pointing and holding questions

The following queries now always include the latest RGB frame and gaze crop:

```text
What am I pointing at?
What am I holding?
What is in my right hand?
```

Hand tracking stores confidence, wrist position, palm position, and palm/wrist normals when those fields are available. Object identification remains approximate unless a calibrated hand-ray-to-camera projection is added later.

### Wake-word variants

The system accepts a narrow set of observed transcription variants only after “Hey”:

```text
Hey Meta
Hey Mera
Hey Mana
Hey Mehta
Hey Metta
Hey Meter
```

This improves recall without treating arbitrary speech as a wake request.

### Concise model sensor context

Raw VIO JSON is saved to the sensor snapshot but is not copied into the OpenAI prompt. The model receives a context of at most 500 characters containing selected gaze, hand, pose, movement, PPG-status, and barometer fields.

### Audio conversion check (carried over from V4)

The SDK stream reports `int64` audio values such as `-1114112` and `1245184`. These equal `-17 * 65536` and `19 * 65536` — signed PCM samples stored with 16 shift bits. The conversion restores them with an arithmetic right shift by 16.

Verify this at every startup. The banner must read:

```text
conversion=signed-q16-shift-int64
```

If it reports `signed-clipped-int64`, the conversion has fallen through to the clipping fallback and every negative sample is being mapped to +32767, producing an apparent ~31k RMS carrier that looks like audio and is not. Stop and fix before recording.

### PPG research estimate

PPG is continuously recorded. A pulse estimate is attempted only when:

- at least 30 seconds of PPG are available;
- the signal is non-flat;
- head-motion RMS is below the configured threshold;
- the dominant spectral peak is within 42–180 bpm; and
- spectral peak confidence exceeds the configured threshold.

The result is explicitly research-only and is not a medical measurement. Rejected estimates retain a status such as `need_longer_window`, `rejected_due_to_motion`, or `low_spectral_confidence`.

## Setup

Requires macOS or Linux. The Project Aria Client SDK supports Mac Big Sur+, Fedora 36+ and Ubuntu 22.04+ on Python 3.10–3.12; there is no Windows build.

```bash
conda activate MetaAriaGlasses
cd /path/to/aria_gen2_watch_and_tell_latest_v5_1
cp .env.example .env     # then set OPENAI_API_KEY
chmod 600 .env
chmod +x *.sh
python -m pip install -r requirements.txt
./check_setup.sh
```

`check_setup.sh` byte-compiles every module and runs both test files, so no separate compile step is needed.

The `.env` should retain an empty transcription prompt:

```properties
OPENAI_API_KEY=YOUR_VALID_KEY
OPENAI_MODEL=gpt-5.6
OPENAI_TRANSCRIBE_MODEL=gpt-4o-transcribe
OPENAI_TRANSCRIPTION_LANGUAGE=en
OPENAI_TRANSCRIPTION_PROMPT=
WATCH_USER_ID=P001
WATCH_DATA_DIR=./data
```

## Run

Keyboard mode:

```bash
./run_keyboard.sh
```

Suggested checks:

```text
What is the capital of India?
What is your name?
What is this?
What am I looking at?
What am I pointing at?
```

Wake mode:

```bash
./run_wake.sh
```

Remain quiet during the three-second calibration. Then say the complete request continuously:

```text
Hey Meta, what is the capital of India?
Hey Meta, what am I looking at?
Hey Meta, what am I pointing at?
```

Type `q` and press Enter to stop cleanly.

## Output layout

```text
data/
├── watch_and_tell_log.csv
├── audio/
├── images/
├── responses/
└── sensors/
    └── P001_YYYYMMDD_HHMMSS/
        ├── manifest.json
        ├── P001_..._all_streams.vrs/
        │   └── ...timestamp....vrs
        ├── streams/
        │   ├── imu_imu-left.jsonl
        │   ├── imu_imu-right.jsonl
        │   ├── eye_gaze.jsonl
        │   ├── hand_pose.jsonl
        │   ├── vio.jsonl
        │   ├── vio_high_frequency.jsonl
        │   ├── ppg.jsonl
        │   └── ...
        └── query_snapshots/
            └── P001_<record-id>.json
```

## Inspect the latest session

```bash
python inspect_sensor_session.py
```

Inspect a specific session:

```bash
python inspect_sensor_session.py data/sensors/P001_YYYYMMDD_HHMMSS
```

The inspector displays callback availability, manifest counts, fallback JSONL counts when needed, dropped events, query snapshots, VRS files, clean-close status, and file sizes.

## Study-use checklist

Before formal participant recording, verify:

- `closed_cleanly: true` in `manifest.json`;
- non-zero counts for required streams;
- `dropped_jsonl_events` is empty or understood;
- the VRS file exists and has a plausible size;
- query snapshots and CSV sensor paths are present;
- pointing answers are treated as approximate;
- PPG estimates are retained as research-only values with quality status.
