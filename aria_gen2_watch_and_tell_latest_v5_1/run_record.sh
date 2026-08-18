#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
# .env is optional -- load_dotenv() tolerates a missing file, and every
# value it could carry (WATCH_USER_ID, WATCH_DATA_DIR, ARIA_IP_ADDRESS) is
# also settable as a plain CLI arg / shell env var, as below.
[[ -f .env ]] && echo "Loaded .env" || echo "No .env found, using CLI args / shell env vars"

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
