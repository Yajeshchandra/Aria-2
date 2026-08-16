# Low-Level Design

Companion to `design/HLD.md`. Schemas, formats, and algorithms. Where a decision is still genuinely open research, it's marked **TBD** rather than given fake precision — see `PROBLEM-STATEMENT.md` §8 for why.

---

## 1. Identifiers

| ID | Format | Set by |
|---|---|---|
| `participant_id` | existing V5.1 convention, e.g. `P001` | intake |
| `story_id` | short slug, e.g. `story_03` | story content |
| `scene_id` | `story_id` + scene index, e.g. `story_03_scene_2` | story content |
| `question_id` | `scene_id` + `_q`, e.g. `story_03_scene_2_q` | story content |
| `option_id` | `question_id` + option index, e.g. `story_03_scene_2_q_opt1` | story content |

Position (`opt1`..`opt4`) is arbitrary and must **not** be assumed to map to a fixed foundation — see §4.

---

## 2. QR payload format

Each scene/question page's QR encodes a single string:

```
<page_type>:<id>
```

Examples: `scene:story_03_scene_2`, `question:story_03_scene_2_q`.

`page_type` lets the sync layer tell scenes and questions apart without a lookup table. Generation is a few lines against the `qrcode` Python package — one image per page, embedded wherever the presentation tool allows a page image.

**Decode side:** sample the RGB stream (not every frame — every 3rd–5th is enough given a QR doesn't disappear in one frame), run a `pyzbar`/OpenCV decode, and on a hit log:

```json
{"qr_payload": "question:story_03_scene_2_q", "timestamp_ns": 1234567890123456, "device_id": null}
```

into the same events stream as everything else in §3.

---

## 3. Events log

One JSONL file per session, alongside the existing `sensors/<participant>_<session>/streams/*.jsonl` files V5.1 already produces. Each line:

```json
{
  "event": "qr_detected",
  "timestamp_ns": 1234567890123456,
  "payload": {"qr_payload": "question:story_03_scene_2_q"}
}
```

Other event types reuse the same shape: `session_start`, `session_end`, `mfq2_start`, `mfq2_end`. This generalizes the "condition" tagging flagged as needed back in `docs/codebase-review-v5_1.md` — instead of tagging one condition per session, it now tags every scene/question boundary within a session.

---

## 4. Foundation-tagging schema (handed to whoever supplies story content)

```json
{
  "question_id": "story_03_scene_2_q",
  "options": [
    {"option_id": "story_03_scene_2_q_opt1", "text": "...", "foundation": "care"},
    {"option_id": "story_03_scene_2_q_opt2", "text": "...", "foundation": "authority"},
    {"option_id": "story_03_scene_2_q_opt3", "text": "...", "foundation": "loyalty"},
    {"option_id": "story_03_scene_2_q_opt4", "text": "...", "foundation": "fairness"}
  ]
}
```

`foundation` ∈ `{care, fairness, loyalty, authority, sanctity}`. Not every decision needs all five represented — coverage is expected to aggregate across the full story set, not within one question. Position of a given foundation should vary across questions (a participant shouldn't be able to learn "option 2 is always the loyalty one").

**Requirement to flag to the content team, per `docs/IKS-vs-MFT.md`:** the story set as a whole should not be skewed toward care/fairness-style dilemmas — deliberately include enough loyalty/authority/sanctity-coded decisions that the aggregate profile isn't measuring a truncated version of the theory.

---

## 5. Sensor data schema — reused, not rebuilt

The existing `sensor_recorder.py` JSONL schema (eye gaze, IMU, PPG, VIO, etc.) is reused as-is — documented in full in `docs/codebase-review-v5_1.md` §1–2. No changes needed to that schema for this design; the only new consumer is the offline feature-extraction step in §6 below, which reads it relative to decision windows instead of relative to a spoken query.

---

## 6. Decision window and feature extraction

**Window definition** (formalizing `PROBLEM-STATEMENT.md` §6): `[t_onset, t_click]` where `t_onset` is the first `qr_detected` event for that `question_id`, and `t_click` is taken as the `qr_detected` timestamp of the *next* page (the following scene or question), used as a proxy since the presentation tool's own submit timestamp isn't reliable at page-turn grain. Re-reading/scrolling within this window is included, not trimmed.

| Feature | Source | Computed as | Status |
|---|---|---|---|
| Gaze allocation across options | eye gaze stream | dwell time / fixation count per option region, requires known on-screen option positions | **TBD** — needs the final presentation tool's layout to define option regions |
| Pupil response | eye camera frames, via `projectaria_tools` offline extraction from VRS | normalized pupil diameter over the window | **TBD** — normalization approach (per-participant baseline vs. per-session) not yet decided |
| Head-motion dynamics | IMU stream | spectral band energy + stillness ratio over the window (extends the existing single-scalar gyro-RMS already used for PPG gating in `sensor_recorder.py`) | defined, not yet implemented |
| Cardiac signal | nosepad PPG | reuse the existing BPM estimator (`_experimental_bpm` in `sensor_recorder.py`) run per-window rather than per-query | defined, reuses existing code |
| Choice latency | events log | `t_click - t_onset` | defined |
| Confidence rating | presentation tool response log | as reported, 1–5 | defined |

Per egoEMOTION's own results (`docs/egoEMOTION-paper-summary.md`): expect head-IMU and pupil to carry the most signal, PPG to be the weakest predictor (kept mainly as a validation channel, not a primary feature) — same priority ordering, now re-applied to discrete decision windows instead of continuous reading.

---

## 7. MFQ-2 scoring

Standard published scoring: sum item responses per subscale (care, fairness, loyalty, authority, sanctity), following the instrument's own published scoring key. Not reimplemented here — administered once at intake, scored exactly as the instrument specifies, no custom logic.

---

## 8. Profile computation — TBD, marked as open research, not engineering

Candidate approach, **not yet validated**:

```
foundation_score[f] = Σ over decisions where chosen option's foundation == f
                        of (1 / conflict_weight)
```

where `conflict_weight` is derived from the physiological features in §6 — high measured conflict discounts that decision's contribution to the tally, on the reasoning (from Greene et al., cited in the problem statement) that a high-conflict choice may reflect situational pressure more than stable foundation weighting.

This is a hypothesis about *how* to combine signal and choice, not a settled formula. RQ1 in `PROBLEM-STATEMENT.md` is precisely whether some version of this — simple tally vs. conflict-weighted tally — agrees better with MFQ-2. Don't build downstream tooling that assumes conflict-weighting works before RQ1 has an answer; build both the plain tally and the weighted version, and compare.

---

## 9. Code changes needed (V6) — see `ROADMAP.md` Goal 1 for sequencing

- Verify the clock-epoch bug (`docs/codebase-review-v5_1.md` B1) before anything else — it can silently zero out every sensor summary.
- Strip V5.1 to a record-only mode: remove wake-word detection, the OpenAI Q&A loop, TTS. Confirmed via the `ponytail-audit` pass already run over the codebase.
- Add the events-log writer (§3) as a new lightweight consumer of the existing RGB and IMU callback pattern in `sensor_recorder.py` — same "degrade, don't crash" style already used for every other callback there.
- Add the QR decode step (§2) as a new consumer of the existing `rgb_callback` in `watch_and_tell_aria_gen2.py`.
- No change needed to eye gaze, IMU, or PPG callbacks — already registered and working.
