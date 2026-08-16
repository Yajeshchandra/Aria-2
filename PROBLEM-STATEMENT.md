# Problem Statement

**Project:** VR Based Storytelling using ML
**Platform:** Meta Aria Gen 2 egocentric research glasses
**Version:** draft 2 — 2026-08-17 (supersedes draft 1; see `HISTORY.md` for what changed and why)
**Status:** core design settled. Story content, participant count, and final presentation tooling still open (§8).

---

## 1. Statement

People make moral judgments constantly, and rarely by consciously applying a rule — the judgment arrives first, the reasoning follows. Standard measurement of moral character relies on questionnaires that ask people to *report* their values in the abstract. This project asks a different question: **can a person's moral-foundations profile be recovered from how they actually behave and physiologically respond while making embodied moral choices inside a first-person narrative — not just from what they say about themselves afterward?**

Participants read short first-person story scenes on a screen, wearing Meta Aria Gen 2 glasses. Each scene ends in a decision: four options, each representing a different moral foundation (care, fairness, loyalty, authority, sanctity). Across many such decisions, spanning multiple stories, two things are recorded: which option they chose, and — via the glasses — how they got there: where they looked, how their pupils and heart rate moved, how their head behaved, how long they took, how sure they said they were.

The claim under test is that the *choice alone* is a noisy signal, and that physiological reactivity during deliberation can refine it into a more reliable profile — one that can be checked, quantitatively, against a validated psychological instrument.

---

## 2. Background

### 2.1 Moral Foundations Theory

Moral Foundations Theory (MFT), developed by Jonathan Haidt, proposes that moral judgment draws on a small set of evolved "foundations" rather than a single good/bad axis:

| Foundation | Core intuition |
|---|---|
| Care/Harm | protecting others from suffering |
| Fairness/Cheating | reciprocity, not being cheated |
| Loyalty/Betrayal | standing with one's group |
| Authority/Subversion | respecting legitimate structure and tradition |
| Sanctity/Degradation | purity, avoiding degradation |

No foundation is inherently superior — people and cultures differ in how heavily they weight each one. This directly matches the project's own framing: *morality is not fundamentally good or bad.*

MFT is not a framework imported onto this study from outside. It descends directly from anthropologist Richard Shweder's "Big Three" ethics (Autonomy, Community, Divinity), derived from fieldwork substantially conducted in **Bhubaneswar, Orissa** — a Hindu temple town — alongside a Chicago comparison sample. See `docs/IKS-vs-MFT.md` for the full treatment, including the finding that MFT's *individualizing* foundations (Care, Fairness) map less cleanly onto Dharmic ethics than its *binding* foundations (Loyalty, Authority, Sanctity), and that this is empirically corroborated by cross-cultural validation of the **MFQ-2** questionnaire, the instrument used here.

### 2.2 Why glasses, why narrative

Aria Gen 2 puts eye tracking, a nosepad PPG sensor, head IMUs, and an egocentric camera into a single 75-gram unit, worn without disrupting behavior. First-person narrative is the delivery mechanism for morally loaded scenarios — it is the medium, not the object of study — because it induces psychological engagement with a dilemma more directly than an abstract questionnaire item ever could.

---

## 3. The problem, stated specifically

### P1 — Does physiological signal during deliberation add real information beyond the choice itself?

If a moral-foundations profile can be built by simply tallying which option (which foundation) gets picked across many decisions, that is a scoring rubric — it needs no glasses and no ML. The physiological question is whether **conflict, hesitation, and engagement during the seconds before a choice** carry information that a bare tally discards: two people can pick the same option, one instantly and one after visible struggle, and a tally treats them identically. Prior work (Greene et al.'s dual-process findings) shows exactly this kind of autonomic/deliberative signature exists for moral dilemmas measured with skin conductance and reaction time in a lab. Whether it is recoverable from egocentric glasses, during a repeated multi-scene task, is untested.

### P2 — Which modalities carry that signal at a discrete decision point?

Unlike continuous narration, this task's signal is anchored to short, repeated, structurally similar events — a decision screen, a choice, a click. Which of gaze allocation across the four options, pupil response, head motion, cardiac signal, response latency, and self-rated confidence actually distinguishes low-conflict from high-conflict choices is not established for this task shape.

### P3 — Does MFT's structure and foundation-weighting hold for this population and this measurement method?

MFQ-2 has been validated on Indian samples as a questionnaire and its five-factor structure holds. Whether the same structure holds when morality is measured through *embodied forced choice* rather than *Likert-scale self-report*, and whether the binding-foundation emphasis documented in the cross-cultural literature (`docs/IKS-vs-MFT.md`) shows up in this study's specific population, is an open empirical question this project can answer directly.

---

## 4. Gap in prior work

The closest prior work remains **egoEMOTION** (arXiv:2510.22129): Aria glasses, 43 participants, eye video, nosepad PPG, head IMU, egocentric RGB, reference ECG/EDA/respiration, self-reported valence/arousal/dominance and Big Five personality, leave-one-subject-out evaluation. Full result tables are in `docs/egoEMOTION-paper-summary.md`.

**This project's earlier design (Velten script-reading, superseded — see `HISTORY.md`) argued its novelty through a voice channel and a no-device control, neither of which egoEMOTION had.** Under the current design, neither of those differences applies: there is no voice channel here either, and no no-device control condition here either (see §7, out of scope). The delta argument had to change, and it is now a **construct** difference rather than a modality difference:

- **egoEMOTION measures general affect and personality; this project measures moral-foundation-specific decision-making.** Their closest analog — personality prediction — landed at or below chance (F1 0.59 vs 0.53 random, several traits worse than chance). Free-standing trait prediction from passive/naturalistic signal did not work in the closest available prior attempt. This project targets something structurally different: a **forced-choice, foundation-tagged, repeated-event design**, cross-validated against a real instrument (MFQ-2) rather than left to stand alone.
- **The task is event-anchored, not continuous.** egoEMOTION's features are statistical descriptors over ~48-second clips or multi-minute activities. This project's signal is tied to short, comparable, repeated decision moments — closer to an event-related design — which supports within- and across-participant comparison at matched moments in a way continuous narration does not.
- **Classical ML, not deep learning, is still the ceiling.** egoEMOTION showed deep learning underperforming classical methods at N=43 (continuous affect: classical 0.75 vs. DCNN 0.68 vs. transformer 0.60). This project will not exceed that N. Same constraint, still worth stating as a deliberate choice rather than a limitation discovered later.

---

## 5. Research questions

**RQ1 (primary).** Can a moral-foundations profile built from repeated forced-choice decisions, refined by physiological deliberation signal, be shown to agree with an independently administered MFQ-2 score?

**RQ2 (primary).** Which modalities — gaze allocation across the four options, pupil response, head-IMU dynamics, cardiac signal, choice latency, self-rated confidence — carry information about deliberation conflict at a moral decision point?

**RQ3 (secondary).** Does this population show the individualizing/binding foundation-weighting pattern documented in the cross-cultural MFT literature (`docs/IKS-vs-MFT.md`), and does story-set balance across foundations affect what's detectable?

**RQ4 (exploratory).** Does the physiological conflict signal from RQ2 correlate with self-rated choice confidence — an internal validity check on whether "conflict" as measured by sensors matches what conflict feels like to the participant?

---

## 6. Approach

**Task.** Multiple stories, each 1–5+ scenes. Each scene is a short first-person passage followed by a four-option decision; each option is tagged (in the data, not necessarily visibly) with the moral foundation it represents. Position of a given foundation is not fixed across decisions. Scene order is **linear per story** (fixed sequence, choices don't alter later content) by default — this keeps stimuli comparable across participants; true branching remains available later without rebuilding anything, since it doesn't change the core outcome being measured.

**Starting session size** (not fixed, adjust after piloting): ~5 stories × 4 decisions ≈ 20 decisions per participant, 45–60 minutes including MFQ-2 intake and breaks — comparable in scale to egoEMOTION's ~70-minute, ~16-labeled-event session.

**Presentation.** A page-per-scene/question tool (Google Forms or equivalent — final tool not fixed, requirement is only "QR support and a clean multiple-choice layout"). Selection by on-screen click; no spoken responses.

**Timing ground truth.** A unique QR code on every scene/question page, decoded from Aria's own RGB stream. The presentation tool supplies **what** was chosen (its response log); Aria supplies **when** each page was shown, on the same clock as every sensor. Full rationale in `docs/design-after-mentor-answers.md`-adjacent discussion, formalized in `design/LLD.md`.

**Decision window.** From the QR-detected onset of a question page to the logged click. Re-reading or scrolling back to the scene text counts as part of the window, not noise to trim.

**Physical setup.** Fixed screen/tablet position, controlled ambient lighting — required for pupil measurement to reflect arousal rather than the room.

**Labels.**
- **Behavioral** — which option (foundation) chosen at each decision, from the presentation tool's log.
- **Self-report per decision** — a confidence rating ("how sure were you"), cheap and left in by default.
- **Reference** — MFQ-2 administered once at intake, used to validate the derived profile.

---

## 7. Scope

**In scope**
- A record-only, event-tagged Aria Gen 2 capture system (V6, see `ROADMAP.md` Goal 1)
- QR-based scene/question timing alignment
- A synchronized corpus: choice, confidence rating, gaze, pupil, IMU, PPG, egocentric RGB, all time-aligned to scene/question boundaries
- Offline feature extraction at decision windows: gaze allocation across options, pupil response, head-motion dynamics, cardiac signal, latency
- A behavioral moral-foundations profile, refined by physiological conflict signal, validated against MFQ-2
- Classical machine learning, subject-independent (leave-one-subject-out) evaluation
- RQ1–RQ4 reported at whatever power the achieved sample supports

**Out of scope**
- Any VR headset — Aria replaces it entirely; the project title reflects the literature it supersedes, not the hardware used
- A no-Aria control condition — dropped for this study given session-length cost; device-reactivity is a separate question for a future study if wanted
- Spoken/prosodic analysis — no voice channel in this design; selection is by click
- Deep learning — ruled out by prior evidence at larger N than this study will reach
- Free-standing personality prediction — prior evidence puts this at or below chance
- Story content authoring — stories are externally supplied; this project's obligation is only to specify the foundation-tagging data format they must arrive in (see `design/LLD.md`)
- Real-time or on-device inference — all analysis is offline

---

## 8. Open items

| # | Item | Owner | Consequence if unresolved |
|---|---|---|---|
| 1 | **IRB/ethics approval not started.** Must cover eye imagery, PPG, egocentric video, bystanders, data retention. | Student + mentor | Hard blocker, longest lead time in the project. |
| 2 | **Sample size undecided.** | Mentor | Determines whether RQ1 is an ML result or a feasibility pilot. |
| 3 | **Presentation tool not finalized** — only the requirement (QR support, clean multiple-choice layout) is fixed. | Student | Gates the QR-generation and page-layout work in `ROADMAP.md` Goal 1. |
| 4 | **Story content and foundation-tagging not yet supplied.** | External / content team | Nothing downstream of content — piloting, feature extraction, profile scoring — can start without at least one complete, correctly tagged story. |
| 5 | **Foundation coverage balance across the story set** — risk of over-representing Care/Fairness-style Western-shaped dilemmas at the expense of Loyalty/Authority/Sanctity, per `docs/IKS-vs-MFT.md`. | Content team, flagged by student | Under-elicits the foundations most likely to be diagnostic in this population. |

---

## 9. Success criteria

1. **System.** V6 records every condition with complete sensor coverage, QR-based scene/question alignment, and verified cross-stream synchronization reported in milliseconds.
2. **Corpus.** A documented, synchronized, foundation-labeled dataset of choices, confidence ratings, and physiological signal at each decision — the durable artifact, independent of any hypothesis surviving.
3. **RQ2 answered.** Modality-wise conflict signal reported per decision, with effect sizes.
4. **RQ1 answered.** Profile-vs-MFQ-2 agreement reported quantitatively, whatever the result.
5. **RQ3 answered.** Foundation-weighting pattern reported against the IKS/MFT literature prediction.
6. **RQ4 explored.** Conflict-signal-vs-confidence correlation reported descriptively.

---

## 10. Contribution, in one sentence

> This project measures moral-foundation-relevant physiological conflict during repeated, embodied, egocentric-glasses-recorded moral choices — cross-validated against a standard psychological instrument, in a population where that instrument's own foundation-weighting is not guaranteed to hold the way it does in the samples it was originally built on.

---

## References

- egoEMOTION: Egocentric Vision and Physiological Signals for Emotion and Personality Recognition — arXiv:2510.22129 (`docs/egoEMOTION-paper-summary.md`)
- Moral Foundations Theory, Jonathan Haidt — [moralfoundations.org](https://moralfoundations.org/)
- Shweder's Big Three ethics and their Bhubaneswar fieldwork origin, and their divergence from Dharmic ethics — `docs/IKS-vs-MFT.md`
- Greene et al., dual-process moral judgment — physiological/reaction-time correlates of moral dilemma conflict
- Full project history and superseded designs — `HISTORY.md`
