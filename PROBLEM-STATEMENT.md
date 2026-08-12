# Problem Statement

**Project:** VR Based Storytelling using ML
**Platform:** Meta Aria Gen 2 egocentric research glasses
**Version:** draft 1 — 2026-08-12
**Status:** four design questions still open (§8). Everything else is settled.

---

## 1. Statement

Research on emotion during narrative has historically required a laboratory: a VR headset or screen to deliver the stimulus, and a rack of body-worn instruments — chest ECG, finger electrodermal sensors, respiration belts — to measure the response. These setups produce clean data at the cost of ecological validity. The participant is wired, seated, and visibly instrumented, and the conditions under which they feel anything bear little resemblance to the conditions under which people ordinarily feel things.

Meta Aria Gen 2 offers a possible substitute. A single 75-gram pair of glasses carries eye-tracking cameras, a nosepad photoplethysmography (PPG) sensor, head IMUs, a spatial microphone array, a contact microphone that isolates the wearer's own voice, and an egocentric RGB camera. If the affective and physiological signals that previously required a lab can be recovered from glasses, the study of emotion during narrative can move into ordinary rooms.

**This project asks whether that substitution holds for a speaking participant, and whether the glasses themselves distort the behaviour they are meant to measure.** Participants read prepared first-person emotional scripts aloud while instrumented, under conditions that vary both the emotional content of the script and the presence of the glasses.

---

## 2. Background

### 2.1 Why storytelling

Narrative is the medium, not the object of study. Reading first-person self-referent statements aloud is a validated mood-induction method — the Velten procedure, in use since 1968 — in which participants read prepared statements and are instructed to feel and experience each as personally applicable. Combined mood-induction procedures built on Velten statements achieve large effects against neutral controls (Hedges *g* ≈ 1.28 for sadness, ≈ 1.35 for joviality, N = 445). Individual Velten statements carry published valence and arousal norms.

The paradigm gives three things a free-narrative task cannot: known effect sizes for power analysis, stimulus-level affect norms independent of participant self-report, and word-for-word comparability of the speech signal across every participant.

### 2.2 Why Aria Gen 2

The device consolidates into one unobtrusive unit what previously took several instruments:

| Signal | Sensor | Replaces |
|---|---|---|
| Cardiac | Nosepad PPG, 128 Hz | Chest ECG |
| Ocular | 2× eye cameras, 90 fps/eye | Desk-mounted eye tracker |
| Motion | Head IMUs, 800–1000 Hz | Motion capture |
| Voice | Contact microphone (own-voice isolation) | Lapel microphone |
| Scene | RGB + 4 SLAM cameras | Fixed room cameras |

The contact microphone is specific to Gen 2 and central here: it separates the participant's speech from the experimenter's and the room's in hardware, which every prosodic measure depends on.

---

## 3. The problem, stated specifically

Three things are unknown.

### P1 — Can glasses-borne sensors recover affect from a *speaking* participant?

Existing evidence covers participants who watch, play, and act. It does not cover participants who talk. Sustained speech changes the measurement problem in three ways:

- **It adds a modality.** Prosody — fundamental frequency, jitter, shimmer, energy contour, speech rate, pause structure — becomes available and is a well-established affective carrier.
- **It contaminates the physiology.** Speaking restructures respiration, which propagates into heart-rate variability and PPG morphology. Cardiac features measured during speech are not comparable to cardiac features measured at rest.
- **It changes the ocular signal.** Gaze during reading aloud is governed by reading mechanics, not scene exploration.

Whether affect remains recoverable under these conditions, and which modalities survive, is untested.

### P2 — Does wearing the glasses change the behaviour being measured?

The ecological-validity argument for egocentric glasses rests on an assumption of non-interference. That assumption is largely unexamined. The available evidence points the other way: the presence of recording technology — fixed cameras, drones, and smart glasses specifically — raises measured anxiety relative to an unobserved condition.

If wearing the glasses alters vocal delivery, gaze, or arousal during an emotionally loaded reading task, then every glasses-based affect measurement inherits a bias, and the "scalable real-world" claim requires qualification. **No existing egocentric affect dataset includes a no-device control condition.**

### P3 — Does the nosepad PPG agree with a reference cardiac sensor?

The PPG is the sensor that makes the physiological claim possible, and it sits on a moving head rather than a chest. Its agreement with a reference measure under a realistic task — including during speech, when respiration is irregular — has not been characterised in this setting.

---

## 4. Gap in prior work

The closest existing work is **egoEMOTION** (arXiv:2510.22129): Project Aria glasses, 43 participants, ~50 hours, eye video, nosepad PPG, head IMU and egocentric RGB, with reference ECG/EDA/respiration worn simultaneously. Self-reported valence, arousal and dominance on a 7-point scale. Leave-one-subject-out evaluation.

Their results establish the baseline this project must be positioned against:

| Task | Best F1 | Random |
|---|---|---|
| Continuous affect (V/A/D, binary) | 0.75 | 0.59 |
| Discrete emotion (9-class) | 0.46 | 0.11 |
| Big Five personality | 0.59 | 0.53 |

And by sensor group:

| Sensor set | Continuous affect | Discrete emotion |
|---|---|---|
| Reference wearables (ECG, EDA, respiration) | 0.70 | 0.28 |
| Aria glasses only | **0.74** | **0.52** |

Glasses outperformed the reference rig. That result is the strongest existing support for the substitution premise — and it also means **"Aria sensors predict valence/arousal/dominance" is not an available contribution.**

Four gaps remain open, and this project's design addresses each:

1. **No speech.** Participants did speak in two of their tasks, but audio appears nowhere in their feature set or results. The microphones were running; the analysis was never done.
2. **No no-device control.** Every participant wore the glasses in every recording. P2 above is untested by construction.
3. **Sparse coverage of the low-arousal/low-valence quadrant** — stated in their own limitations. Velten negative scripts target precisely this region.
4. **Retrospective self-report labels**, which they identify as subject to recall bias and unable to capture dynamics.

Two further findings from that work directly constrain this project's design:

- **Deep learning underperformed classical methods** at N = 43 (continuous affect: classical 0.75, CNN 0.68, transformer 0.60). At smaller N, engineered features with classical models are the appropriate ceiling.
- **Nosepad PPG was among the weakest modalities** — 0.12 F1 on 9-class emotion against a 0.11 random baseline, i.e. at chance. Head IMU was the strongest single modality (0.44). This reframes PPG as a validation target (P3) rather than a primary predictor.

---

## 5. Research questions

**RQ1 (primary).** Can affective state during first-person script reading be recovered from Aria Gen 2 sensors, and which modalities carry the signal when the participant is speaking?

**RQ2 (primary).** Does wearing Aria Gen 2 measurably change vocal delivery, ocular behaviour, or self-reported affect during an emotionally loaded reading task?

**RQ3 (secondary).** How closely does Aria's nosepad PPG agree with a reference cardiac sensor during speech and at rest?

**RQ4 (exploratory).** Does eye–voice span — the interval by which gaze leads the voice during reading aloud — vary with the emotional content of the text? This measure requires synchronised gaze, own-voice audio, and known text, and is computable in this design and not in prior egocentric datasets.

---

## 6. Approach

Within-subjects. Each participant completes all conditions; order counterbalanced.

| Condition | Task | Device | Serves |
|---|---|---|---|
| C1 | Read emotional first-person script aloud | Aria worn | RQ1, RQ4 |
| C2 | Read emotional first-person script aloud | No Aria | RQ2 |
| C3 | Read neutral first-person script aloud | Aria worn | RQ1 control |

The conditions form a 2×2 with one cell deliberately empty:

|  | **Aria worn** | **No Aria** |
|---|---|---|
| **Emotional script** | C1 | C2 |
| **Neutral script** | C3 | *(not run)* |

- **C1 vs C3** isolates emotional content. Speaking, reading, gaze target and task load are held constant, so any difference is attributable to the text.
- **C1 vs C2** isolates device presence, with identical text on both sides.

> **Deviation from the original brief.** The mentor's stated third condition is "no storytelling with Meta Aria." Substituting a neutral script for silence is a proposed change, and it follows Velten practice, which has always included a neutral statement set. As specified, C1 vs C3 would confound emotional content with speaking, reading, gaze target and cognitive load simultaneously, and no difference found could be attributed to emotion. **This substitution requires mentor approval.**

**Instrumentation.** Aria Gen 2 full sensor suite in C1 and C3. A reference chest-strap cardiac monitor and an external microphone worn in **all three** conditions — this gives C2 a measurable signal and simultaneously supplies the reference channel for RQ3.

**Labels.** Participant self-report after every block: valence, arousal and dominance on a SAM-style scale, plus pre- and post-condition affect. Emotion Regulation Questionnaire once at intake.

---

## 7. Scope

**In scope**
- A silent, condition-aware recording system on Aria Gen 2 (V6), built from the existing V5.1 streaming and sensor infrastructure
- A synchronised multimodal corpus: eye, PPG, IMU, own-voice audio, RGB, with block-level event markers and self-report labels
- Feature extraction: reading eye movements, eye–voice span, prosody, head-motion dynamics, cardiac
- Classical machine learning with subject-independent (leave-one-subject-out) evaluation
- Reporting of RQ1–RQ4 at whatever power the achieved sample supports

**Out of scope**
- Any VR headset. The project title reflects the prior literature Aria replaces; no virtual reality hardware is used.
- Deep learning. Ruled out by prior evidence at larger N than this study will reach.
- Personality prediction. Prior results are at or below chance.
- Free or autobiographical narrative. Scripts are prepared in advance.
- Clinical, diagnostic or medical interpretation of any physiological measure.
- Real-time or on-device inference. All analysis is offline.

---

## 8. Open items

These block data collection and are not yet resolved.

| # | Item | Owner | Consequence if unresolved |
|---|---|---|---|
| 1 | **Ethics/IRB approval not started.** Must cover eye imagery, PPG, egocentric video, bystanders, data retention, and any third-party API transmission of participant speech. | Student + mentor | Hard blocker. Longest lead time in the project. |
| 2 | **Sample size undecided.** | Mentor | Determines whether RQ1 is a machine-learning result (N ≈ 20–40) or a feasibility pilot (N < 15). RQ2 is adequately powered at smaller N given *g* ≈ 1.3 within-subjects. |
| 3 | **C3 substitution (neutral script for silence) requires approval.** | Mentor | Without it, the primary within-device contrast is confounded and RQ1 is not answerable. |
| 4 | **"Regulation" undefined** in the original brief. Proposal: measure as both trait (ERQ at intake) and outcome (pre→post affect change). | Mentor | Both instruments are questionnaires and cost nothing; collecting both removes the need to resolve the ambiguity beforehand. |

---

## 9. Success criteria

Ordered so that the project produces a defensible result even if the sample is small.

1. **System.** V6 records all conditions with continuous own-voice audio, complete sensor coverage, block-level event markers, and verified cross-stream synchronisation reported in milliseconds.
2. **Corpus.** A documented, synchronised, labelled dataset — the durable artifact, and the deliverable that does not depend on any hypothesis surviving.
3. **RQ3 answered.** PPG-versus-reference agreement is a methods result computable from a small sample and reportable regardless of everything else.
4. **RQ2 answered.** Device-presence effect reported with an effect size and confidence interval, including a null result if that is what the data shows.
5. **RQ1 answered.** Modality-wise affect recovery under speech, evaluated leave-one-subject-out against a random baseline, positioned explicitly against the egoEMOTION figures in §4.
6. **RQ4 explored.** Eye–voice span reported descriptively; treated as exploratory.

---

## 10. Contribution, in one sentence

> Prior work has shown that egocentric glasses can read affect from someone watching; this project asks whether they can read it from someone speaking — adding a voice channel that prior egocentric datasets never analysed, targeting the low-arousal-negative region those datasets under-sample, and running the no-device control that no egocentric affect study has yet included.

---

## References

- egoEMOTION: Egocentric Vision and Physiological Signals for Emotion and Personality Recognition — arXiv:2510.22129
- Velten mood induction, combined-procedure validation (N = 445) — [PMC6548374](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6548374/)
- Valence and arousal ratings for Velten mood induction statements
- Eye–voice coordination in text reading aloud — [PMC10452879](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10452879/)
- Emotional vignettes versus pictures, eye tracking — [PMC7264705](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7264705/)
- Under the camera eye: surveillance technology, performance and anxiety — [Springer](https://link.springer.com/article/10.1007/s00779-025-01846-8)
- Aria Gen 2 device and SDK documentation — [projectaria.com](https://www.projectaria.com/glasses/)
