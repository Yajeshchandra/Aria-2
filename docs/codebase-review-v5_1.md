# V5.1 Codebase Review — `aria_gen2_watch_and_tell_latest_v5_1`

Read in full: 2723 lines across 15 files. This reviews the code as-is, then against the storytelling study it has to support.

**Correction to `research-space-map.md`:** that document said eye tracking and PPG were "not in V5.1." That was based on the abstract in `v5_1.md`, and it's wrong about the real code. `sensor_recorder.py` registers eye gaze, PPG, hand pose, and VIO callbacks. What's missing is not the *capture* — it's the *feature extraction*. Different problem, addressed in P4 below.

---

## 1. What this actually is

A voice assistant on Aria Gen 2, with a multimodal recorder bolted alongside it.

```
"Hey Meta, what am I looking at?"
   │
   ├─ mic ch7 → ring buffer → VAD gate → OpenAI STT → wake regex
   │                                          │
   │                                          ├─ vision hint? → RGB frame + gaze crop
   │                                          ├─ sensor snapshot → ≤500-char context
   │                                          └─ GPT → answer → render_tts on glasses
   │
   └─ (in parallel, always) 13 sensor callbacks → JSONL + VRS + manifest
```

Two files carry it:

| File | Lines | Role |
|---|---|---|
| `watch_and_tell_aria_gen2.py` | 1258 | connect, stream, audio ring buffer, wake VAD, STT, LLM, TTS, CSV log |
| `sensor_recorder.py` | 776 | 13 callbacks, JSONL writer thread, manifest thread, rolling history, PPG BPM |

Everything else is scaffolding: two run scripts, a setup checker, a session inspector, two test files, four markdown docs.

### Modes
- **keyboard** — press Enter, speak ≤4–6 s, get an answer.
- **wake** — RMS-gated VAD on channel 7, 4 s window, "Hey Meta" regex, then answer.

Both are **short-utterance Q&A**. Hold that thought; it's the crux of section 3.

---

## 2. What is genuinely good

Not padding. These are real and they should survive into V6.

### 2.1 The Q16 audio discovery (`_to_pcm16`, lines 106–159)

The SDK was handing back `int64` values like `-1114112` and `1245184`. Someone noticed those are `-17 × 65536` and `19 × 65536` — signed PCM in Q16 fixed point, not full-scale audio. The naive `np.clip` maps every negative sample to +32767 and produces a ~31k RMS carrier that looks like a signal and isn't.

The fix checks `np.all(raw & 0xFFFF == 0)` before arithmetic-right-shifting by 16, and falls through four other dtype cases with named diagnostics (`signed-q16-shift-int64`, `unsigned-low16-uint16`, …). `test_audio_conversion.py` pins three of them.

This is hardware debugging that most people would never find. It is the single most valuable thing in the repo, and it would have silently poisoned every audio feature in the study.

### 2.2 PPG that refuses to lie (`_experimental_bpm`, lines 488–573)

Linear detrend → Hann window → `rfft` → restrict to 0.7–3.0 Hz → peak-to-median ratio → BPM. Gated by five separate refusals:

| Status | Trigger |
|---|---|
| `insufficient_data` | < 30 samples |
| `need_longer_window` | < 30 s duration |
| `rejected_due_to_motion` | gyro RMS > 0.35 rad/s |
| `flat_signal` | std ≤ 1e-9 |
| `outside_plausible_range` | BPM outside 42–180 |
| `low_spectral_confidence` | peak/median < 4.0 |

Every threshold is a CLI flag. No SciPy dependency — `np.polyfit` + `np.hanning` + `np.fft` do the job.

Emitting a status instead of a number is the correct engineering call. A study that logs 400 confident-looking BPM values, half of them head-motion artifacts, is worse than one that logs 200 values and 200 honest refusals.

### 2.3 Shutdown ordering (`stop`, lines 474–534)

```
stop_tts → stop_streaming → sleep(drain) → clear_callbacks → sleep(0.25)
        → stop_server → sensors.close() → null the handles
```

Guarded by `_stop_lock` + `_stopped` so signal handler and `finally` can't double-run it. The comment states the reasoning: no callback should write after the native receiver stops. Plus the manifest is checkpointed every 5 s, so a hard crash still leaves accurate counts on disk.

Race-free teardown of a native pybind11 streaming stack is a thing people usually get wrong.

### 2.4 Degrade-don't-die callback registration (lines 447–460)

```python
method = getattr(self.stream_receiver, method_name, None)
if method is None:
    self.sensors.mark_unavailable(method_name)
```

Runs against any SDK version. Missing streams are recorded in the manifest rather than crashing the session. Combined with `_to_jsonable`'s depth-limited attribute probing, the recorder tolerates SDK objects it has never seen.

### 2.5 VRS authoritative, JSONL derived

Stated explicitly in code comments, the README, and the manifest `note` field. Correct architecture: the raw record is immutable and complete; JSONL is the convenient decoded view you're allowed to regenerate.

### 2.6 Tests exist and are honest

Four synthetic tests (`test_v5_1.py`) plus three conversion cases. `test_ppg_estimate` injects a real 72 bpm sinusoid and asserts recovery within 2 bpm. `test_motion_rejection` injects the same signal with high gyro and asserts the refusal path fires. That's testing behaviour, not implementation.

---

## 3. The gap between this code and the study

The mentor's study is: **three conditions, human participants, first-person storytelling as the medium.** Measured against that, here is what the code does not do.

### P1 — There is no experiment controller

Grep the repo for condition, trial, block, phase, event marker, or session annotation. Nothing.

Participant metadata is one string:
```
--user-id P001   →   data/sensors/P001_20260811_143022/
```

No condition field. No way to mark "story started at t=142 s", "prompt delivered", "participant paused". For a three-condition design you need at minimum a condition label in the session identity and timestamped event markers in a shared clock. Right now the only way to know which condition a session was is to remember which folder you made when.

This is a small change (a `--condition` flag and an events JSONL) and it must happen before anyone is recorded.

### P2 — There is no continuous speech capture — this is the biggest one

Trace it:

- `AudioRingBuffer(max_seconds=20.0)` — a **ring**. Audio older than 20 s is dropped on the floor.
- `capture_question(seconds)` → `sleep(seconds)` → `snapshot(seconds)`. Hard-capped at `--listen-seconds` (4 in `run_keyboard.sh`, 6 by default).
- `logger.save_audio(wav_bytes, record_id)` only fires inside `handle_query` — i.e. only when a question was asked.

So a WAV lands on disk **only at query time, and only ~4 seconds of it**. A 10-minute storytelling monologue produces **zero** WAV files and zero transcripts.

The audio is not *lost* — VRS is recording the full session. But there is no continuous WAV, no continuous transcript, and no code path that produces either. Every prosody feature in the mentor's brief depends on an artifact that this pipeline does not currently create.

V6's central task is a **record-only storytelling mode**: continuous multichannel WAV to disk, continuous transcript with word timings, no wake word, no LLM.

### P3 — The contact microphone is assumed, not wired

Channel 7 is hardcoded in three places (`--audio-channel 7`, `--wake-vad-channel 7`, and the help text "channel 7 is calibrated for wearer speech on this device").

Two things are unclear from the code:
1. **Is channel 7 the nosepad contact mic, or just the spatial mic that happened to be loudest during calibration?** The help text says "on this device," which reads like empirical tuning, not a documented channel map. There is no `register_contact_mic_callback` in `callbacks()`.
2. **How was 7 determined, and does it hold for a different unit or a different streaming profile?**

For a storytelling study this is the highest-value channel in the whole device — it is what separates the participant's voice from the experimenter's and the room's. It deserves a documented channel map and a verification step, not a magic number in a help string. The parameterisation is fine; the missing provenance is not.

### P4 — Eye gaze is logged but never turned into a feature

```python
elif stream in ("eye_gaze", "vio", "hand_pose", ...):
    if rows:
        summary["latest"] = rows[-1][1]
```

That is the entire analysis of eye gaze: the most recent sample. The mentor's brief names **gaze dispersion** as a primary construct, and the literature gives it a standard operationalisation (stationary gaze entropy, gaze transition entropy). None of it is computed.

Same shape of gap for prosody: audio is captured, but there is no F0, jitter, shimmer, energy contour, speech rate, or pause distribution anywhere in the repo.

The good news is this is offline work on already-captured data — it doesn't have to be in the live loop, and it doesn't gate data collection. But nothing in the current `analysis` story (pandas/NumPy/matplotlib, per the abstract) exists as code yet.

### P5 — "Micro-motion" is one scalar

```python
result["movement_intensity"] = float(np.sqrt(np.mean(np.square(gyro_norms))))
```

Gyro-norm RMS. That is correct and sufficient **for its actual job**, which is gating PPG against motion artifacts. It is not "micro-motion patterns": no spectral band decomposition, no stillness ratio, no tremor band, no postural drift. Another offline-feature gap rather than a bug.

### P6 — The assistant is a confound during a storytelling session

If wake mode is running while a participant tells a story:
- a false wake trigger interrupts the narrative,
- the LLM answers something,
- `render_tts` plays audio **out of the glasses' own speakers**, which the glasses' own microphones then record.

That is an uncontrolled stimulus injected mid-narrative and contamination of the audio channel you care about most.

There is no `--record-only` mode. The closest available workaround is keyboard mode with nobody pressing Enter — which happens to work, but by accident rather than design, and it still leaves the wake path a keystroke away.

### P7 — Third-party data flow is an ethics item, not just an engineering one

Every transcription posts participant speech to the OpenAI API. Every vision query posts an RGB frame of the participant's real environment — potentially including bystanders' faces — to the OpenAI API.

This has to be named explicitly in the IRB submission. It is also an argument for the record-only mode in P6: with the LLM path off, no participant data leaves the machine.

The system prompt does include *"Do not identify private people or infer sensitive personal traits"* — good instinct, and worth keeping — but a prompt instruction is not a data-handling control. The data has already been transmitted by the time the model reads it.

---

## 4. Bugs and correctness risks

### B1 — Mixed clock epochs in the rolling history *(verify this first)*

Severity: high. This can silently zero out every sensor summary.

`record()` timestamps events with `_timestamp_ns(payload)`, which prefers a **device** timestamp:
```python
value = _get(payload, "capture_timestamp_ns", "tracking_timestamp_ns",
             "timestamp_ns", "sensor_timestamp_ns", "utc_timestamp_ns")
```
falling back to `_now_ns()` (host Unix epoch) only if none is present. Three callbacks — `_ble_callback`, `_wifi_callback`, `_calibration_callback` — pass `_now_ns()` unconditionally.

Then `snapshot()` does:
```python
now = _now_ns()                              # ≈ 1.75e18 (Unix ns)
cutoff = now - int(analysis_window * 1e9)
... [row for row in rows if ts >= cutoff]
```

Aria's `tracking_timestamp` is **device-boot-relative**, not Unix epoch — on the order of `1e12` for a session minutes old. If the SDK's `capture_timestamp_ns` is on that clock rather than Unix, then every device-timestamped row satisfies `ts < cutoff` and gets filtered out. Result: `samples_in_window: 0` on every stream, empty summaries, no PPG estimate ever, and an empty `model_context` — while `manifest.json` cheerfully reports millions of samples, because `_counts` is incremented before any filtering.

The same mixing feeds `_experimental_bpm`, which derives `fs` from `np.diff(t)` on these timestamps. There is already a guard (`fs = inferred_fs if 5.0 <= inferred_fs <= 512.0 else default`) which would mask a wrong clock rather than surface it.

`test_v5_1.py` cannot catch this — it injects `time.time_ns()`-based timestamps, so the tests only ever exercise the host-clock path. The one case that breaks is the one that never gets tested.

**Check on any real session already recorded:**
```bash
python inspect_sensor_session.py
# then compare manifest counts against a query snapshot's samples_in_window
```
Large counts + `samples_in_window: 0` confirms it. The fix is to normalise every stream onto one clock at `record()` time and keep the device timestamp as a separate field.

### B2 — JSONL volume will drop events on a long session

Every event stores a full `raw` dict via `_to_jsonable`. Two IMUs at ~1 kHz is ~2000 JSON lines/second. Files are opened with `buffering=1` (line-buffered — a syscall per line). The queue holds 100k events, which at that rate is ~50 seconds of slack if the writer falls behind.

A 4-second Q&A never hits this. A 20-minute storytelling session is ~2.4M lines and gigabytes of JSON, most of it duplicating what VRS already holds losslessly.

`dropped_jsonl_events` in the manifest will tell you whether it happened — but it tells you *after* the participant has gone home. Measure it on a full-length dry run before recording anyone. The cheap fix is to stop writing `raw` for high-rate streams; VRS is already the authoritative copy, which is exactly the argument the README makes.

### B3 — Two history-cutoff conventions

`record()` prunes with `cutoff = ts - rolling_seconds*1e9` using the **incoming event's** timestamp. `snapshot()` filters with `cutoff = _now_ns() - analysis_window`. Different reference points on possibly different clocks. Same root cause as B1; worth fixing in the same pass.

### B4 — `_prepare_speech` thresholds are tuned for short utterances

```python
noise_rms   = percentile(frame_rms, 20)
speech_rms  = percentile(frame_rms, 90)
active_threshold = max(noise_rms*1.8, noise_rms+20.0, speech_rms*0.18)
```

Percentile-based gating over a 4-second window where most frames are speech. Over a 10-minute monologue that is mostly *pauses*, the 20th and 90th percentiles describe a completely different distribution, and the aggressive edge-trimming plus `gain = min(12.0, 28000.0/peak)` normalisation would be wrong for continuous capture.

Not a bug in current use. It's a reason the record-only path in P2 should write raw continuous audio and leave `_prepare_speech` to the Q&A path only.

### B5 — Platform

Confirmed against Meta's docs: **Client SDK platform support is Mac Big Sur+, Fedora 36+, Ubuntu 22.04+. Windows is not supported.** Python 3.10–3.12.

This repo agrees: `.sh` scripts throughout, `lsof` in `check_setup.sh`, and README paths under `/Users/squarebracket/…`.

The working directory here is Windows 11. **Collection has to happen on the Mac.** Analysis code (pandas/NumPy on recorded JSONL/VRS) runs anywhere, so the split is: capture on macOS, analysis wherever. Worth confirming before planning any session around this machine.

### B6 — Minor

- `audio_callback` computes `raw.min()`/`raw.max()` on every packet, then discards them unless `_audio_debug_printed` is False. Trivial waste; ~free to fix.
- `_encode_gaze_crop` maps yaw/pitch to pixels through hand-entered FOV constants (110°/90°) with no lens distortion model. The docstring says so honestly and the full frame is always sent alongside. Fine as a heuristic, must not become a measurement.
- The wake variant list (`meta, metta, mehta, mera, mana, meter`) is empirical and only matches after "hey" — a deliberately narrow design. Reasonable. Just note it is tuned to one accent and one STT model.

---

## 5. What V6 needs, ordered

Everything here is prerequisite to recording participants.

| # | Change | Why | Size |
|---|---|---|---|
| 1 | **Verify B1** on a real recorded session | If summaries are silently empty, nothing downstream is trustworthy | 10 min |
| 2 | **`--condition` flag + events JSONL** with start/stop/prompt markers | Three-condition design is unrunnable without it | small |
| 3 | **`--record-only` mode**: no wake, no LLM, no TTS | Removes the confound (P6) and keeps participant data local (P7) | small |
| 4 | **Continuous multichannel WAV writer** | The single biggest gap (P2). Nothing else substitutes | medium |
| 5 | **Continuous transcript with word timings** | Every prosody-over-narrative-time analysis depends on it | medium |
| 6 | **Verify the channel map** — is ch7 the contact mic? Document it | Highest-value channel is currently a magic number (P3) | 30 min |
| 7 | **Full-length dry run**, check `dropped_jsonl_events` and VRS size | Catches B2 before a participant is affected | 1 session |
| 8 | **Measure cross-stream sync**, don't assert it | Clap/flash test; report residual in ms. Every multimodal claim rests on this | 1 session |
| 9 | Offline feature extraction: gaze entropy (SGE/GTE), prosody, motion bands | P4/P5. Post-collection, so it does not gate anything | large, deferrable |

Items 1–8 are days of work, not weeks. Item 9 is the actual research and can wait until there's data.

---

## 6. Verdict

The engineering is better than the abstract suggested. The Q16 discovery, the refusing PPG estimator, and the shutdown ordering are all things a careful engineer did on purpose, and the code says why in comments. That is not typical of student research code.

What it isn't is a study instrument. It's a **voice assistant with excellent telemetry**, and the study needs a **silent recorder with an experiment controller**. Those overlap in the plumbing — connection, streaming, sensor callbacks, VRS, manifest, clean shutdown are all done and all reusable — and diverge completely in the interaction layer. Roughly 60% of V5.1 carries over untouched; the wake/LLM/TTS layer gets a switch put in front of it rather than being deleted.

One correction worth carrying into the mentor conversation: eye gaze and PPG **are** already being captured. What's missing is the feature extraction on top. That's a better position to be in than the `v5_1.md` abstract implied.

---

## Sources

- [Project Aria Client SDK setup — platform support](https://facebookresearch.github.io/projectaria_tools/docs/ARK/sdk/setup)
- [Aria Gen 2 Client SDK installation](https://facebookresearch.github.io/projectaria_tools/gen2/ark/client-sdk/start)
- [projectaria-client-sdk (PyPI)](https://pypi.org/project/projectaria-client-sdk/)
- [Aria Gen 2 Documentation](https://facebookresearch.github.io/projectaria_tools/gen2/)
