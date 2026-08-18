#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
[[ -f .env ]] || { echo "Missing .env. Run: cp .env.example .env && nano .env"; exit 2; }

if [[ -z "${1:-}" && -z "${WATCH_USER_ID:-}" ]]; then
  echo "Usage: ./run_record.sh <participant_id>  (or set WATCH_USER_ID in .env)"
  exit 2
fi

python -u watch_and_tell_aria_gen2.py \
  --profile profile9 \
  --user-id "${1:-}" \
  --ip-address "${ARIA_IP_ADDRESS:-}" \
  --rotate-image 0 \
  --qr-scan-interval-seconds 0.5 \
  --enable-sensors \
  --save-sensors \
  --record-vrs \
  --sensor-rolling-seconds 45 \
  --sensor-manifest-interval-seconds 5 \
  --sensor-close-timeout-seconds 20 \
  --shutdown-drain-seconds 2 \
  --ppg-window-seconds 30 \
  --ppg-min-duration-seconds 30 \
  --ppg-default-sample-rate 128 \
  --ppg-motion-gyro-threshold 0.35 \
  --ppg-peak-ratio-threshold 4 \
  2>&1 | tee "record_session_${1:-session}.log"
