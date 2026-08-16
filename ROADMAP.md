# Roadmap

Three sequential goals. Each depends substantially on the one before it, though some overlap is expected (piloting straddles Goal 1 and Goal 2; feature-extraction code can be written against synthetic data before Goal 2 finishes). Checkboxes are for tracking — this file is meant to be edited as work happens, not archived.

See `PROBLEM-STATEMENT.md` for what and why, `design/HLD.md` / `design/LLD.md` for how.

---

## Goal 1 — Build the codebase (V6)

Turn V5.1, a voice assistant with excellent telemetry, into a silent, event-tagged recorder.

- [ ] Verify the clock-epoch bug (`docs/codebase-review-v5_1.md` B1) on a real recorded session — 10 minutes, blocks trusting any sensor summary until checked
- [ ] Strip to record-only mode: remove wake-word detection, the OpenAI Q&A loop, TTS
- [ ] Apply the cuts identified in the `ponytail-audit` pass (unused web-search feature, redundant raw-JSON duplication, unused hand-pointing feature) — not blocking, but do it while the file is already open for the record-only strip
- [ ] Add the events-log writer (`design/LLD.md` §3) — session/scene/question boundary markers
- [ ] Add the QR decode step (`design/LLD.md` §2) as a new RGB-callback consumer
- [ ] Confirm eye gaze, IMU, and PPG callbacks still register and produce data in record-only mode — should be unaffected, verify anyway
- [ ] Set up `projectaria_tools` on the analysis machine (any platform) for offline eye/hand feature extraction from VRS
- [ ] Full-length dry run: run the whole recorder through one complete mock session, check `dropped_jsonl_events`, verify VRS file size is plausible
- [ ] Measure cross-stream sync in milliseconds — clap/flash test, don't assert it
- [ ] Confirm collection happens on macOS/Linux — the Client SDK has no Windows build

## Goal 2 — Experiments & data collection

- [ ] **IRB submission — start this now, in parallel with Goal 1.** Longest lead time in the project, zero code dependency. Must name eye imagery, PPG, egocentric video, bystanders, data retention.
- [ ] Receive story content with foundation tags in the format specified in `design/LLD.md` §4
- [ ] Check story-set foundation balance against `docs/IKS-vs-MFT.md` — flag if it's skewed toward care/fairness-style dilemmas
- [ ] Finalize the presentation tool (Forms or equivalent) and build the QR-embedded page set
- [ ] Set up MFQ-2 administration (intake, before the story task)
- [ ] Pilot on self, then a small group — validate timing, sync, session length, comfort; adjust the ~5-stories/~20-decisions starting point from `PROBLEM-STATEMENT.md` §6 based on what's actually tolerable
- [ ] Get a final participant count from the mentor (`PROBLEM-STATEMENT.md` §8, item 2 — still open)
- [ ] Run full data collection

## Goal 3 — ML inference

- [ ] Offline feature extraction per decision window (`design/LLD.md` §6): gaze allocation across options, pupil response, head-IMU dynamics, PPG-derived cardiac signal, choice latency
- [ ] Compute the plain behavioral tally (foundation counts from choices alone) — the baseline everything else has to beat
- [ ] Compute the conflict-weighted profile (`design/LLD.md` §8) — the actual hypothesis under test
- [ ] Cross-validate both against MFQ-2 scores — RQ1
- [ ] Modality-wise analysis of which signals carry deliberation-conflict information — RQ2
- [ ] Foundation-weighting analysis against the IKS/MFT literature prediction — RQ3
- [ ] Conflict-signal-vs-confidence-rating correlation — RQ4
- [ ] Classical ML only (SVM/Random Forest-class), leave-one-subject-out evaluation — no deep learning, per the egoEMOTION precedent at comparable N
- [ ] Write up results against `PROBLEM-STATEMENT.md` §9 success criteria
