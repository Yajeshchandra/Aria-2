# Changelog

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
