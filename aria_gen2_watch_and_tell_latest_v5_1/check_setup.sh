#!/usr/bin/env bash
set -u
cd "$(dirname "$0")"

fail=0
check_cmd() {
  if command -v "$1" >/dev/null 2>&1; then
    printf "[pass] %-18s %s\n" "$1" "$(command -v "$1")"
  else
    printf "[fail] %-18s not found\n" "$1"
    fail=1
  fi
}

check_cmd python
check_cmd aria_doctor
check_cmd aria_gen2

python - <<'PY' || fail=1
mods = ["aria.sdk_gen2", "aria.stream_receiver", "openai", "numpy", "PIL", "dotenv"]
for name in mods:
    try:
        __import__(name)
        print(f"[pass] import {name}")
    except Exception as exc:
        print(f"[fail] import {name}: {exc}")
        raise
PY

if [[ -f .env ]]; then
  echo "[pass] .env exists"
  python - <<'PY' || fail=1
from pathlib import Path
from dotenv import dotenv_values
v = dotenv_values(Path('.env'))
key = (v.get('OPENAI_API_KEY') or '').strip()
print('[pass] OPENAI_API_KEY is present' if key else '[fail] OPENAI_API_KEY is empty')
print('[info] OPENAI_MODEL =', v.get('OPENAI_MODEL') or '(default)')
print('[info] OPENAI_TRANSCRIBE_MODEL =', v.get('OPENAI_TRANSCRIBE_MODEL') or '(default)')
print('[info] OPENAI_TRANSCRIPTION_PROMPT is', 'set' if (v.get('OPENAI_TRANSCRIPTION_PROMPT') or '').strip() else 'empty (recommended)')
if not key:
    raise SystemExit(1)
PY
else
  echo "[fail] .env missing (copy .env.example to .env)"
  fail=1
fi


python -m py_compile \
  watch_and_tell_aria_gen2.py \
  sensor_recorder.py \
  inspect_sensor_session.py \
  test_audio_conversion.py \
  test_v5_1.py || fail=1

echo "--- Local conversion/sensor tests ---"
python test_audio_conversion.py || fail=1
python test_v5_1.py || fail=1

if lsof -nP -iTCP:6768 -sTCP:LISTEN >/dev/null 2>&1; then
  echo "[warn] TCP port 6768 is already in use:"
  lsof -nP -iTCP:6768 -sTCP:LISTEN
else
  echo "[pass] TCP port 6768 is free"
fi

echo "--- Aria device list ---"
aria_gen2 device list || fail=1

echo "--- Python SDK connection/authentication test ---"
python - <<'PY' || fail=1
import aria.sdk_gen2 as sdk_gen2
client = sdk_gen2.DeviceClient()
client.set_client_config(sdk_gen2.DeviceClientConfig())
device = client.connect()
print(f"[pass] connected/authenticated: {device.connection_id()}")
PY

exit "$fail"
