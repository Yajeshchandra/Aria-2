# Changelog

## 6.0.0 — 2026-08-17

Reshaped from a voice assistant into a silent, QR-synced recorder for the moral-choice study. Full reasoning trail in `../HISTORY.md`; architecture in `../design/HLD.md` and `../design/LLD.md`.

- **Removed**: wake-word detection (`WAKE_VARIANTS`, `WAKE_PATTERN`, `run_wake_mode`), the OpenAI Q&A loop (`ask_openai`, `handle_query`, web-search routing), text-to-speech (`speak`), all live audio-question capture (`AudioRingBuffer`, `_prepare_speech`, `_mono_from_multichannel`, `transcribe`), gaze-guided vision cropping, `DataLogger` (CSV/image/audio/response artifacts). No voice channel exists in the current study design.
- **Removed**: `hand_pose` and `vio_high_frequency` sensor callbacks — both existed only to support the removed pointing/holding voice queries; neither feeds any feature in `design/LLD.md`'s decision-window feature table.
- **Removed**: `--mode keyboard`/`--mode wake` distinction — there is one mode now, silent recording. `run_keyboard.sh` and `run_wake.sh` replaced by `run_record.sh`.
- **Removed**: `test_audio_conversion.py` — its subject, `AudioRingBuffer._to_pcm16`, no longer exists. The Q16 conversion knowledge is preserved in this README's "Audio conversion note," not in code, since nothing currently decodes live PCM.
- **Fixed**: cross-stream clock alignment. `SensorRecorder.record()` now captures a host-clock `received_ns` alongside the device-reported `timestamp_ns` and uses `received_ns` exclusively for windowing/cutoff decisions (`snapshot()`, rolling-history pruning). Device timestamps on a different epoch than host time (a real, confirmed failure mode — some SDK builds report boot-relative timestamps) could previously cause every sample to be silently filtered out of a window while `manifest.json` still reported full counts. Device `timestamp_ns` is still used where it's the physically correct clock, e.g. PPG sample-rate inference. Covered by `test_v5_1.py::test_mixed_clock_origin_windowing` — the earlier test suite only ever exercised host-clock-consistent timestamps, which is why this didn't surface sooner.
- **Added**: QR-based scene/question sync. `_scan_for_qr` decodes the latest RGB frame every `--qr-scan-interval-seconds`; a new code is logged to a new `events` JSONL stream via the existing generic `SensorRecorder.record()` path. `generate_qr.py` produces the QR images for a page list.
- **Removed**: `model_context`, `_numbers`, `_fmt` from `sensor_recorder.py` — dead code once `handle_query` (their only caller) was removed.
- **Removed**: duplicated `"raw": _to_jsonable(...)` field from IMU, eye-gaze, VIO, barometer, magnetometer, and PPG callback payloads — VRS already holds the lossless raw record; JSONL already extracts the named fields these callbacks care about. Kept as-is for GPS, phone-location, Bluetooth/Wi-Fi, and calibration callbacks, where the generic conversion *is* the only representation, not a duplicate of one.
- **Removed**: `openai` dependency (no longer called anywhere). **Added**: `qrcode`, `pyzbar`.
- **Removed**: OpenAI-related `.env` keys (`OPENAI_API_KEY`, `OPENAI_MODEL`, `OPENAI_TRANSCRIBE_MODEL`, `OPENAI_TRANSCRIPTION_LANGUAGE`, `OPENAI_TRANSCRIPTION_PROMPT`) — `.env.example` now only carries `WATCH_USER_ID` / `WATCH_DATA_DIR`.
- **Changed**: participant ID is now required (`--user-id` or `WATCH_USER_ID`) — the recorder refuses to auto-generate one for a study session.

## Housekeeping — 2026-08-12

Documentation only. No code, no behaviour change.

- Removed `MIGRATION_FROM_V5.md`. The V5 to V5.1 migration is complete and the file described a one-time move.
- Removed `README_V4_FIX.md`. Its content is now the "Audio conversion check" section of `README.md`, which additionally states the failure symptom to watch for.
- Removed `install_dependencies.sh`. Its only unique step, `pip install -r requirements.txt`, is now in the README setup block; `check_setup.sh` already byte-compiled the modules and ran both test files.
- `README.md` setup now states the platform requirement (macOS/Linux, Python 3.10–3.12 — the Client SDK has no Windows build), uses a generic path instead of a machine-specific one, and copies `.env.example` rather than a sibling V5 checkout.

## 5.1.0

- Keeps the validated V4 Q16-shifted audio conversion and channel-7 wearer-speech path.
- Adds a shutdown lock, two-second native drain, explicit callback clearing when available, and final sensor-recorder closure after the receiver stops.
- Adds `q`, `quit`, `exit`, or `stop` as clean wake-mode shutdown commands.
- Checkpoints the sensor manifest every five seconds and finalizes session counts, end time, queue state, and clean-close status.
- Adds JSONL line-count fallback to the sensor-session inspector.
- Makes pointing and holding questions visual, so the current RGB frame and gaze crop are included.
- Adds structured hand confidence, wrist, palm, and palm-normal values when exposed by the SDK.
- Accepts a small observed set of wake-transcription variants after “Hey”: Meta, Metta, Mehta, Mera, Mana, and Meter.
- Replaces raw/truncated VIO JSON in the model prompt with a concise sensor context capped at 500 characters.
- Extends rolling sensor history for a 30-second PPG window.
- Adds motion-screened, spectral-quality-checked, research-only pulse estimation with explicit status and confidence fields.
- Adds synthetic tests for Q16 audio conversion, PPG estimation, motion rejection, manifest finalization, and JSONL integrity.

## 5.0.0

- Added continuous raw VRS and decoded JSONL recording for all available sensor callbacks.
- Added per-query sensor snapshots, gaze-guided vision, hand context, and initial PPG/movement summaries.
