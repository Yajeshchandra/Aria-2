# Project History

Chronological log of how this project's understanding evolved. Purpose: so nobody — including future-us — re-derives or re-argues a settled decision. If a document elsewhere in this repo contradicts this file, this file is more recent and wins; the older document is left in place as a record of the reasoning at the time, not deleted.

---

## 2026-08-11 — Initial exploration

Mentor brief was ambiguous: title "VR Based Storytelling using ML," a rationale paragraph naming valence/arousal/dominance/regulation and gaze dispersion/prosody/micro-motion, and a bare three-condition procedure. Mapped seven plausible interpretations rather than committing to one — instrument-validation, narrative-as-regulation (Pennebaker), affect recognition, machine-as-storyteller, immersion transfer, device reactivity, dataset-building. Researched Aria Gen 2's actual sensor suite, egoEMOTION as closest prior work, gaze-entropy literature, and expressive-writing research.

→ `docs/research-space-map.md`

**Key early finding:** the mentor's own sentence — "Aria enables the transition *from* controlled VR-based... *to* scalable real-world environments" — meant VR was being *replaced*, not used. No headset was ever part of this project.

## 2026-08-11 — Mentor Q&A

Ten questions put to the mentor. Answers resolved: no VR headset ("Aria replaces everything"); within-subjects design confirmed; "first-person storytelling" clarified as the participant *reading a prepared script*; labels come from self-report; eye tracking and PPG confirmed in engineering scope.

That last clarification — reading a script — was recognized as the **Velten Mood Induction Procedure**, a validated paradigm since 1968 with published effect sizes and stimulus norms. Design converged on Velten script-reading with self-reported valence/arousal/dominance as the target.

→ `docs/design-after-mentor-answers.md`

## 2026-08-11 — Full codebase review

Read all 2,723 lines of `aria_gen2_watch_and_tell_latest_v5_1/` (V5.1). Found genuinely strong engineering — a hard-won fix for a Q16 fixed-point audio bug, a PPG estimator that refuses to report an unreliable pulse rather than guessing, race-free native-SDK shutdown. Also found the system was built as a **voice assistant**, not a silent recorder: no continuous speech capture (a 10-minute reading would produce zero audio files), a possible clock-epoch bug that could silently zero out sensor summaries, no condition/event tagging, and confirmed the Client SDK has no Windows build — collection has to happen on macOS.

→ `docs/codebase-review-v5_1.md`

## 2026-08-11/12 — egoEMOTION read in full, with real numbers

Extracted the actual result tables (not just the abstract). Established: glasses alone (F1 0.74 affect / 0.52 discrete emotion) beat a full reference physiological rig (0.70 / 0.28); classical ML beat deep learning at N=43; head IMU was the single best modality; nosepad PPG was at chance for discrete emotion (0.12 vs 0.11 random); personality prediction failed outright. Their stated limitations — retrospective self-report labels, sparse low-arousal/low-valence coverage, no speech analysis despite participants speaking in two tasks — became the basis for this project's novelty argument at the time.

→ `docs/egoEMOTION-paper-summary.md`

## 2026-08-12 — Repository cleanup

No git history existed in the tree, so deletions were treated as permanent. Removed three superseded files (`MIGRATION_FROM_V5.md`, `README_V4_FIX.md`, `install_dependencies.sh`), preserving their content into `README.md` and `CHANGELOG.md` before deletion. Ran a `ponytail-audit` over the codebase — identified ~350 cuttable lines (an unused web-search feature, redundant raw-JSON duplication given VRS is already the authoritative record, an unused hand-pointing feature) — findings recorded, not yet applied to the code.

Reorganized the root directory: reference documents moved into `docs/`, `PROJECT.md` created as a one-page index for a project that had accumulated enough documents to get disorienting.

## 2026-08-17 — Major pivot: the actual assignment

The mentor's real task turned out not to be mood induction at all: participants read a first-person passage, then face a **branching decision with four options, each representing a different moral framing**, repeated across multiple scenes and multiple stories. The Velten mood-induction design was superseded at this point.

**What this changed:**
- The target stopped being a mood rating (valence/arousal/dominance) and became a **moral-foundations profile**.
- "Gaze dispersion" and "reading dynamics" (fixation duration, eye–voice span) — the sensor-priority conclusions built for continuous script-reading — stopped applying. There is no continuous reading-aloud in this design.
- The three-condition structure (with-Aria / without-Aria / no-storytelling) no longer mapped onto anything in the new task shape.

## 2026-08-17 — ML target resolved

Discussion surfaced the real fork: predict the choice (redundant — the participant already reports it), tally choices into a profile (doesn't need sensors at all), or characterize the *physiological conflict* behind each choice. Landed on a synthesis: **a moral-foundations profile computed from choice pattern, refined by physiological conflict signal during deliberation, validated against a real questionnaire.** This is the only framing where Aria's sensors are doing something a plain multiple-choice form couldn't.

## 2026-08-17 — Framework and logistics resolved

- Framework: **Moral Foundations Theory** (Care, Fairness, Loyalty, Authority, Sanctity), validated against **MFQ-2**.
- Story content: externally supplied — "assume stories to be given," Delightex (the platform first mentioned) dropped as a project concern, kept only as a possible content source.
- Presentation: a page-per-scene tool (Google Forms-shaped, not finalized) — selection by click.
- **No spoken responses in this design** — a real, named trade-off: the contact-mic/prosody advantage the Velten design had over egoEMOTION no longer applies here.
- **No-Aria control condition (C2) dropped** for this study, by recommendation — doubling session length wasn't justified once the core question shifted from device-reactivity to moral profiling. Flagged as overridable.
- Timing ground truth: a **QR code per scene/question page**, decoded from Aria's own RGB stream — chosen over a spoken scene-boundary marker specifically because speaking would (a) pollute an otherwise-empty audio channel and (b) break the immersion the whole task depends on.

## 2026-08-17 — Indian Knowledge System vs. Moral Foundations Theory

Researched whether MFT — now the chosen framework — is even appropriate for a likely-Indian participant population. Finding: MFT is not a foreign import; it descends directly from Richard Shweder's fieldwork, conducted substantially in **Bhubaneswar, Orissa**. But the individualizing foundations (Care, Fairness) map more weakly onto Dharmic/Varnashrama ethics than the binding foundations (Loyalty, Authority, Sanctity) — a pattern independently corroborated by MFQ-2's own cross-cultural validation data. Practical consequence: use **MFQ-2**, not the older MFQ-30; don't over-load the story set with Care/Fairness-style Western dilemmas.

→ `docs/IKS-vs-MFT.md`

## 2026-08-17 — Documentation restructured for publication

`PROBLEM-STATEMENT.md` rewritten to match the current design (draft 2 supersedes draft 1). `design/HLD.md`, `design/LLD.md`, `ROADMAP.md`, and this file added.

## 2026-08-17 — External chat dump reviewed

A shared ChatGPT conversation (from "squarebracket," the V5.1 author, per the hardcoded path in the old README) was pasted in for review. Two genuinely useful findings, one thing flagged as a different, non-current study:

- **Confirmed the clock-epoch bug independently.** Prior analysis of a real V5.1 session explicitly documented that device `timestamp_ns` "may not share the same origin across all streams" and recommended aligning on host-received time instead — upgrading this project's own B1 finding (`docs/codebase-review-v5_1.md`) from hypothesized risk to confirmed issue with a known fix.
- **Got the exact `profile9` sensor rates** (dual IMU 800 Hz, PPG 128 Hz, eye gaze 30 Hz, RGB 5 Hz at 2560×1920, etc.) and, separately, a claim that **profile9 does not include raw eye-tracking camera video** — if true, this would remove pupil/blink/Fisherface features (`docs/egoEMOTION-paper-summary.md` Tier 1) from what's obtainable under this profile, not just from what's obtainable live vs. offline. Flagged as needing verification against real hardware, not yet confirmed.
- **A separate "Meta Aria Moral Learning Study"** described in the same dump (Banyan Deer Jataka tale, AI-dialogue vs. matched-text vs. moral-cue-control, EEG + Aria, testing lesson *retention*) is a different, likely earlier or parallel study from the same lab — not the branching-choice/MFT design this project builds. Noted as probable lineage for "storytelling to study morality," not as something to build against.

## 2026-08-17 — V6 built

Wrote the code implementing everything decided above. `aria_gen2_watch_and_tell_latest_v5_1/` bumped to 6.0.0.

- **Clock-epoch fix applied**, not just documented: `sensor_recorder.py`'s `record()` now captures a host-clock `received_ns` alongside the device `timestamp_ns`; all cross-stream windowing keys off `received_ns` only, while `timestamp_ns` is kept for within-stream precision work (PPG sample-rate inference) where it's the physically correct clock. A new test (`test_mixed_clock_origin_windowing`) injects timestamps on an unrelated epoch to prove the fix — the old test suite only ever exercised host-clock-consistent timestamps, which is exactly why B1 wasn't caught earlier.
- **`watch_and_tell_aria_gen2.py` rewritten**, 1258 → ~330 lines, class renamed `StudyRecorderApp`: wake-word detection, the OpenAI Q&A loop, TTS, and all live audio-question capture removed. QR scanning added (`_scan_for_qr`, `run_record_mode`), logging detections through the existing generic JSONL writer — no new writer needed.
- **`hand_pose`/`vio_high_frequency` callbacks and the duplicated `raw` JSON field removed from `sensor_recorder.py`** — the ponytail-audit cuts from 2026-08-12, applied.
- New: `generate_qr.py`, `run_record.sh`. Removed: `run_keyboard.sh`, `run_wake.sh`, `test_audio_conversion.py` (subject no longer exists — the Q16 knowledge is preserved in `README.md` prose, not code).
- Everything testable without the physical device passes: syntax compiles clean, all 5 synthetic tests pass, `generate_qr.py` verified end-to-end. **Not yet verified: anything requiring the Mac + glasses** — live callback registration, a full-length dry run, cross-stream sync in milliseconds, and the profile9-ET-video question above.

---

## Superseded — do not build against these

Kept for the reasoning trail, not current:

| What | Where it lived | Superseded by |
|---|---|---|
| Velten script-reading as the task | `docs/design-after-mentor-answers.md`, `PROBLEM-STATEMENT.md` draft 1 | Branching moral-choice narrative, `PROBLEM-STATEMENT.md` draft 2 |
| Valence/arousal/dominance self-report as the label | same | Moral-foundations profile, cross-validated against MFQ-2 |
| Continuous own-voice audio, prosody, eye–voice span as core modalities | same | No voice channel in the current design |
| Reading-eye-movement features (fixation duration, regression rate specific to reading aloud) | same | Gaze allocation across the four options during deliberation |
| Three-condition with/without-Aria/no-storytelling structure | same | Superseded entirely; no-Aria control dropped, see above |
| V6 build priority list centered on continuous WAV capture and forced-alignment transcription | `docs/codebase-review-v5_1.md` §5 | `ROADMAP.md` Goal 1 — QR/event logging replaces continuous-audio capture as the top engineering priority |

The engineering findings in `docs/codebase-review-v5_1.md` that are **not** design-specific — the Windows/macOS platform split, the shutdown-ordering and PPG-estimator code quality — remain fully current and are not superseded by anything above. The clock-epoch bug specifically has moved from *flagged* to *fixed* — see 2026-08-17, "V6 built," above; `docs/codebase-review-v5_1.md`'s B1 write-up is now a historical description of the bug, not a live risk.
