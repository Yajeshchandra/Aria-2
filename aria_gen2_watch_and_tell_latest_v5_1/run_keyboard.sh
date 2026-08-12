#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
[[ -f .env ]] || { echo "Missing .env. Run: cp .env.example .env && nano .env"; exit 2; }

python -u watch_and_tell_aria_gen2.py \
  --profile profile9 \
  --mode keyboard \
  --listen-seconds 4 \
  --audio-channel 7 \
  --transcription-language en \
  --transcription-prompt "" \
  --audio-debug \
  --enable-sensors \
  --save-sensors \
  --record-vrs \
  --use-sensor-context \
  --gaze-guided-vision \
  --sensor-rolling-seconds 45 \
  --sensor-manifest-interval-seconds 5 \
  --sensor-close-timeout-seconds 20 \
  --shutdown-drain-seconds 2 \
  --ppg-window-seconds 30 \
  --ppg-min-duration-seconds 30 \
  --ppg-default-sample-rate 128 \
  --ppg-motion-gyro-threshold 0.35 \
  --ppg-peak-ratio-threshold 4 \
  --save-data \
  2>&1 | tee keyboard_session_v5_1.log
