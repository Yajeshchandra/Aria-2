# After the Mentor Meeting — What Resolved, What Broke, What's Now Yours

Companion to `research-space-map.md`. That document mapped seven interpretations. Six are now dead. This one records which survived, what the surviving answer costs you, and the three decisions your mentor handed back.

**Date:** 2026-08-11

---

## 1. Scoreboard

| # | Question | Answer | Status |
|---|---|---|---|
| 1 | Real VR headset? | "Aria replaces everything" | **Resolved.** No headset. Title is legacy framing. |
| 2 | Who speaks? | **"reads a script"** | **Resolved — and it changes the study.** See §2. |
| 3 | Within or between? N? | "yes all 3" | **Half resolved.** Within-subjects confirmed. **N still unanswered.** |
| 4 | IRB status? | "idk" | **Unresolved — critical path. Yours now.** |
| 5 | What's measured in the no-Aria condition? | "idk" | **Unresolved. Yours to propose.** |
| 6 | Where do labels come from? | "participants do it" | **Resolved in principle.** Self-report. Frequency undecided. |
| 7 | What is "regulation"? | "idk" | **Unresolved. Yours to propose.** |
| 8 | Eye tracking + PPG in scope? | "yes" | **Resolved.** Engineering priority confirmed. |
| 9 | System, finding, or dataset? | "all" | **Not scoped.** See §7. |
| 10 | egoEMOTION delta? | "you tell me" | **Handed back.** Answered in §6. |

Four answers, three "idk"s, one deferral, one question thrown back. That's a normal mentor meeting. The "idk"s are not obstruction — they're the mentor telling you these are your calls to make and bring back.

---

## 2. The big one: "reads a script" means this is Velten

Everything in `research-space-map.md` assumed the participant might be generating narrative. They aren't. They're reading prepared first-person text aloud.

That paradigm already exists and has since 1968.

**The Velten Mood Induction Procedure:** participants read aloud a series of self-referent statements, instructed to *"feel and experience each statement as it would apply to you personally."* First person. Read aloud. Progressing from neutral toward a target affective state.

"First-person storytelling where the participant reads a script" is Velten, or a narrative extension of it.

### Why this is good news

| Gain | Detail |
|---|---|
| **Known effect sizes** | Combined mood-induction procedures using Velten statements reach Hedges *g* ≈ 1.28–1.35 for sadness and joviality against neutral (N = 445 validation). You can power the study instead of guessing. |
| **Published valence/arousal norms** | Velten statements have existing V/A ratings in the literature. Free stimulus-level labels, independent of your participants' self-reports. |
| **Perfect cross-subject comparability** | Every participant says the same words in the same order. Prosody is comparable word-for-word — impossible with free narrative. |
| **Forced alignment is trivial** | You know the text in advance. Word- and phoneme-level time alignment is a solved problem when the transcript is given. Every prosodic feature gets a precise time anchor. |
| **Text valence is a designed variable** | Positive, negative, and neutral script sets give you *designed* label variance rather than whatever variance you happened to capture. |
| **Vignettes beat pictures for valence** | Emotional text induces stronger valence effects than equivalent pictures, with comparable arousal. Your elicitor is not a weak one. |

You have gone from "novel paradigm, unknown effect size, uncomparable data" to "50-year-old validated paradigm with published norms." That is a large upgrade in footing.

### Why it costs you something

**Cost 1 — "Gaze dispersion" is dead as specified.**

This is the sharpest consequence and your mentor should hear it directly.

Gaze dispersion (stationary gaze entropy, gaze transition entropy) measures how attention is distributed **across a scene**. A person reading text is not scanning a scene. Their gaze is pinned to a page or screen, executing reading saccades. Computing gaze entropy over that measures *reading layout*, not affective attention. The number will be small, stable, and about typography.

The mentor's rationale paragraph names gaze dispersion as a primary construct bridge. Under the script-reading design, that specific bridge does not hold.

**What replaces it is arguably better.** Reading eye movements are a mature measurement literature with established affective sensitivity:

| Feature | Why it works here |
|---|---|
| Fixation duration per word | Longer under load; sensitive to word-level valence |
| Regression rate | Re-reading — a load and comprehension-difficulty marker |
| Reading rate | Perceived positive text valence attracts *shorter* reading times than negative — a validated effect you can replicate as a positive control |
| **Eye–voice span** | How far the eyes lead the voice while reading aloud. Compresses under cognitive and emotional load. Requires exactly what you have: gaze + own-voice audio + known text |

Eye–voice span is the standout. It is only computable when you have synchronized gaze, speech, and ground-truth text simultaneously — which is precisely the intersection Aria Gen 2 plus a script gives you, and which no headset study and no passive-viewing dataset can produce.

So: don't tell your mentor gaze is unusable. Tell them the *construct changes* from scene-scanning dispersion to reading dynamics, and that the replacement is better instrumented.

**Cost 2 — The third condition is now badly matched.**

C1 is "read a first-person script aloud." C3 is "no storytelling." The contrast between them confounds at least four things at once:

- speaking vs. silent
- reading vs. not reading
- eyes on text vs. eyes on room
- task load vs. rest

Any difference you find between C1 and C3 could be any of those. You cannot attribute it to the emotional content of the narrative, which is the thing you care about.

**The fix is nearly free and it's already the Velten standard: make C3 a neutral script.** Velten has always included a neutral statement set for exactly this reason. If C3 becomes "read a neutral first-person script aloud," then C1 vs C3 differs *only in emotional content* — speaking, reading, gaze target, and load are all held constant. That is a clean contrast instead of a confounded one.

This is a change to the mentor's stated procedure, so it is a proposal, not a decision you make alone. But it is a well-motivated one with 50 years of precedent, and it costs nothing to run.

**Cost 3 — Label variance may collapse.**

If every participant reads the same script and then rates how they felt, ratings will cluster. Clustered labels are *good* for validating the induction ("did the script reliably work?") and *bad* for machine learning (little variance to predict — a model that outputs the mean scores well and has learned nothing).

Mitigations, in order of cost:
1. **Multiple script sets with different valence targets** (positive / negative / neutral). Designed variance. This is standard Velten. Cheap.
2. **Per-segment self-report** — rate after each block rather than once per condition. Turns ~3 labels per person into ~15–30.
3. **Retrospective continuous annotation** on a subset of participants — dense time-series labels.

Without at least (1) and (2), you will not have enough labels to train anything, no matter how many sensors you record.

**Cost 4 — You are measuring performed affect as well as felt affect.**

Reading emotional text aloud produces vocal affect partly because the participant is *enacting* the text and partly because the text is *inducing* a state. Those are different constructs and they are entangled by design in this paradigm.

Not a flaw — Velten has always had this property and the induction demonstrably works. But your self-report labels measure *felt* state while your prosody features substantially capture *performed* state. Name that in the writeup rather than letting a reviewer name it for you. It is also a reason to keep PPG in the analysis: heart rate is much harder to perform than voice.

---

## 3. Where interpretations landed

| Interpretation | Verdict |
|---|---|
| 1. Instrument validation ("can glasses replace the lab") | **Alive — the spine of the project.** Confirmed by "Aria replaces everything." |
| 2. Narrative as emotion regulation (Pennebaker disclosure) | **Dead.** Scripted reading is not self-disclosure. |
| 3. Affect recognition during narrative | **Alive as a component**, not the headline. See §6. |
| 4. Machine generates the story | **Dead.** The script is prepared in advance by the researchers. |
| 5. Immersion / presence transfer | **Weakened.** Reading a script is a low-immersion task. |
| 6. Device reactivity (does Aria change behavior) | **Alive.** C1 vs C2 still stands. Now *stronger*, because identical text makes the two conditions genuinely comparable. |
| 7. Build the dataset and pipeline | **Alive.** "All three" makes this the container for the rest. |

The project is now **Interpretation 1 + 6, with 3 as the ML layer and 7 as the deliverable.** That's coherent — it was the most likely reading and the answers confirmed it.

---

## 4. The three "idk"s — recommendations to bring back

Your mentor didn't refuse these. They handed them to you. Come back with proposals, not questions.

### 4.1 IRB — this is your critical path

Not the code. The code can be finished in a week; an ethics review cannot.

Find out this week which body has jurisdiction (university IRB, department committee, or a Meta-specific research agreement — Project Aria has its own bystander-privacy obligations). Then the submission must explicitly cover:

- **Eye images.** Aria's eye-tracking cameras capture images of the eye region. Depending on jurisdiction this may count as biometric data with separate handling requirements.
- **Heart rate via PPG.** Physiological data. Note in the submission that your own code labels it research-only and non-medical — that framing helps.
- **Egocentric video.** Records the participant's real environment, including anyone who walks through it.
- **Bystanders.** Meta's own Project Aria research policy has requirements here. Read them before writing the protocol, not after.
- **Third-party API transmission.** Under the current code, participant speech goes to OpenAI for transcription and RGB frames go to OpenAI for vision queries. This must be disclosed. **The clean answer is to disable that path for recording sessions entirely** — see §5, item 3. "No participant data leaves the machine" is a far easier sentence to get approved than any explanation of a data-processing agreement.
- **Retention and destruction.** How long, where, who can access, when destroyed.

### 4.2 What to measure in the no-Aria condition

**Recommendation: a chest-strap heart rate monitor plus an external microphone, in all three conditions.**

Reasoning:
- The strap gives you a heart-rate channel in C2, so the device-reactivity contrast is not purely self-report.
- Worn in **all three** conditions, it doubles as **validation of Aria's nosepad PPG against a reference** — which is exactly the "can glasses replace the lab" claim, measured directly rather than asserted. That is a publishable result on its own and it costs one cheap accessory.
- The external mic makes prosody comparable across C1 and C2. Without it, C2 has no speech signal at all and half your features vanish in that condition.
- Total cost: a chest strap and a recorder. Compared to everything else in this project, negligible.

Do **not** propose "Aria worn but secretly not recording" as the no-device condition. It is a deception manipulation, it needs separate IRB justification, and it tests belief rather than device presence.

### 4.3 What "regulation" means

**Recommendation: measure it two cheap ways and let the data decide.**

1. **Trait** — the Emotion Regulation Questionnaire (ERQ), once per participant at intake. Ten items, two minutes, gives you reappraisal and suppression subscales as covariates. Enables analyses like "do habitual suppressors show different prosody while reading negative scripts."
2. **Outcome** — affect measured before and after each condition (PANAS or SAM). The pre→post delta *is* an operational definition of regulation in the mood-induction literature, and you need pre/post measurement anyway to show the induction worked.

Both are questionnaires. Both are free. Together they cover the two plausible readings of the mentor's word, so you don't have to resolve the ambiguity before collecting — you just collect both and report whichever the mentor meant.

Skip the third reading (moment-to-moment regulation process). It needs a speech coding scheme and dense annotation and it is out of scope for one term.

---

## 5. Revised engineering priorities

The V6 list in `codebase-review-v5_1.md` mostly survives, but script-reading reorders it and adds one item.

| # | Change | Changed by the script answer? |
|---|---|---|
| 1 | **Verify the clock-epoch bug (B1)** on a real session | No — still first. Nothing downstream is trustworthy until this is checked. |
| 2 | **`--condition` flag + events JSONL** with block markers | **Bigger now.** Multiple script blocks per condition means you need per-block start/stop markers, not just per-session. |
| 3 | **`--record-only` mode** — no wake, no LLM, no TTS | **Now non-negotiable.** Doubles as the IRB answer: no participant data leaves the machine. |
| 4 | **Continuous multichannel WAV** | Unchanged — still the biggest gap. |
| 5 | **Continuous transcript** | **Easier now.** You have the script in advance, so this becomes *forced alignment* against known text rather than open-vocabulary ASR. Higher accuracy, word-level timings, and it can run offline. |
| 6 | **Verify the channel map** — is channel 7 the contact mic? | **More important.** Own-voice isolation is now the core measurement, not a convenience. |
| 7 | **NEW: script presentation with logged timing** | The participant needs to read from something. Whatever displays it must timestamp when each block appeared, on the same clock as the sensors. Paper won't do this. |
| 8 | Full-length dry run — check `dropped_jsonl_events` | Unchanged. |
| 9 | Measure cross-stream sync in milliseconds | **More important.** Eye–voice span is a millisecond-scale measurement. Your sync error is its noise floor. |
| 10 | Offline features: reading eye movements, eye–voice span, prosody | **Reframed** from gaze dispersion to reading dynamics. Post-collection, doesn't gate anything. |

**On item 7 — how the script is presented is now a design decision, not a detail.** It determines what the eye tracker sees:

| Presentation | Consequence |
|---|---|
| Paper in hand | Head moves with the page; gaze and head motion entangle; no timing log |
| Fixed screen | Stable geometry, clean reading measurements, timing logged for free. **Recommended.** |
| Teleprompter / scrolling | Fixed gaze point; kills most reading-eye-movement features |
| Memorized, then recited | Best for naturalistic gaze; large participant burden; introduces recall variance |

A fixed screen at a known distance is the pragmatic answer: it makes gaze geometry tractable, logs block timing for free, and preserves the reading measurements that replaced gaze dispersion.

---

## 6. Answering the mentor's question: the egoEMOTION delta

Your mentor asked you to make this argument. Here it is, in the form you can say out loud.

**What egoEMOTION already established:** Project Aria glasses, 43 participants, ~50 hours. Eye video at 90 fps, nosepad PPG at 128 Hz, head IMU, egocentric RGB. Self-reported valence/arousal/dominance on a 7-point SAM scale, plus Big Five. Tasks were nine emotion-eliciting video clips and seven naturalistic activities. Baselines: SVM at F1 0.75 on binary V-A-D, Random Forest at 0.46 on nine-class emotion. Their headline finding: eye-tracking features were the most informative modality, and egocentric signals beat conventional physiological baselines.

**So "Aria sensors predict VAD" is taken.** Do not propose that as the contribution. At student N you will not beat 43 participants with reference-grade wearables.

**Four things separate your study, and they compound:**

**1. Speech production. Theirs is entirely receptive.**
Every egoEMOTION task is passive or non-verbal — watching clips, playing Jenga, painting. The participant never produces sustained speech. Your participant is speaking continuously, which means:
- **Prosody exists as a modality at all.** They have no own-voice channel. You have F0, jitter, shimmer, energy contour, speech rate, and pause structure. Aria Gen 2's contact microphone is purpose-built for this and their paradigm gave them no reason to use it.
- **Speech mechanically couples to physiology.** Speaking restructures breathing, which alters heart-rate variability and PPG morphology. This is simultaneously a confound they never had to handle and a signal they could never observe. Either way it is new territory.
- **Gaze during speech production is a different phenomenon** from gaze during passive viewing, with different dynamics and a different feature set.

**2. Eye–voice span is only measurable in your design.**
Gaze plus own-voice plus ground-truth text, synchronized. egoEMOTION has the first, lacks the second, and has no text at all. This measure is unavailable to them in principle, not just in practice — and it is a documented load-sensitive index.

**3. A no-device control. They have none.**
Every egoEMOTION participant wore the glasses for every recording. Nobody has tested whether wearing egocentric sensing glasses changes the behavior being measured. The recording-technology literature says smart glasses raise anxiety relative to no observer. If that holds for your task, it qualifies the ecological-validity claim that the entire "glasses replace the lab" argument rests on — including egoEMOTION's. **Your C2 is a check on their assumption.**

**4. Self-referential induction, not stimulus viewing.**
Their affect comes from watching someone else's content. Yours comes from the participant reading first-person statements about themselves and being instructed to feel them. Self-referential processing is a different mechanism, and the Velten literature gives you effect sizes and stimulus norms that video-clip elicitation does not.

**One-sentence version for the mentor:**

> egoEMOTION showed Aria's sensors can read affect from someone *watching*. We're asking whether they can read it from someone *speaking* — where the voice is a new signal, breathing contaminates the physiology, and nobody has ever checked whether wearing the glasses changes the behavior in the first place.

**Practical gift from their paper:** eye tracking was their most informative modality. That independently confirms the priority your mentor just approved, and it is a citable reason to put eye tracking ahead of RGB in V6.

---

## 7. On "all three" deliverables

"System, finding, and dataset — all" is the mentor declining to scope. That's normal, and it's fine, because at this scale the three nest rather than compete:

```
DATASET  ← the deliverable
  ├─ requires the SYSTEM (V6 recorder + experiment controller)
  └─ enables the FINDING (device reactivity; PPG vs chest-strap validation)
```

Build the system because the dataset needs it. Collect the dataset because it's the durable artifact. Report the findings the dataset supports. If N ends up small, the dataset and system still stand as contributions and the findings get reported as a pilot with effect sizes rather than claims.

**Bring one number back to the mentor: N.** They answered the within/between half of question 3 and skipped the count. It determines everything:

| N | What is honestly claimable |
|---|---|
| < 15 | Feasibility pilot. Descriptive statistics, effect-size estimates, no ML claims. |
| 20–40 | Classical ML on engineered features, subject-wise cross-validation. Paired within-subject tests are adequately powered for *g* ≈ 1.3 effects. |
| > 60 | Learned representations become defensible. Unlikely in one term. |

Note the good news hiding in the Velten effect sizes: at *g* ≈ 1.3 and within-subjects, the *induction check* — did the script move affect at all — is well powered even at N ≈ 15. The ML is what needs the larger N, not the psychology.

---

## 8. Do these next

**This week, no dependencies:**
1. Run `python inspect_sensor_session.py` on any existing session. Compare manifest counts against a query snapshot's `samples_in_window`. Large counts with zeros is the clock-epoch bug — it invalidates every summary until fixed.
2. Find out who owns IRB for this project. One email.
3. Verify whether channel 7 is the contact microphone or just the loudest spatial mic. Document the channel map.
4. Confirm the Mac is the collection machine — the Client SDK doesn't support Windows.

**Bring to the next mentor meeting:**
5. "Reads a script means this is Velten mood induction — here are the published effect sizes and the existing valence/arousal norms for the statements."
6. "Gaze dispersion doesn't survive script reading. Reading dynamics and eye–voice span replace it, and they're better instrumented."
7. "C3 should be a *neutral* script, not silence — otherwise C1 vs C3 confounds emotion with speaking, reading, and load all at once."
8. "Proposal: chest strap in all three conditions. Solves the no-Aria measurement problem and validates Aria's PPG at the same time."
9. "Proposal: ERQ at intake plus pre/post affect. Covers both readings of 'regulation' for the price of two questionnaires."
10. "How many participants?"

---

## Sources

- [Online validation of combined mood induction procedures (PMC6548374)](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6548374/) — Velten effect sizes, N=445
- [Individual differences and response to the Velten mood induction procedure](https://www.sciencedirect.com/science/article/abs/pii/019188699090258S)
- [Valence and Arousal Ratings for Velten Mood Induction Statements](https://www.researchgate.net/publication/226248905_Valence_and_Arousal_Ratings_for_Velten_Mood_Induction_Statements)
- [Mood induction procedures: a critical review](https://pubmed.ncbi.nlm.nih.gov/18558143/)
- [From Abstract Symbols to Emotional (In-)Sights: eye tracking, emotional vignettes vs pictures](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7264705/)
- [How emotional prosody guides your way: evidence from eye movements](https://www.mcgill.ca/pell_lab/files/pell_lab/paulmann_titone__pell_2012.pdf)
- [Eye–voice coordination in text reading aloud](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10452879/)
- [egoEMOTION](https://arxiv.org/html/2510.22129)
- [Under the camera eye: surveillance technology, performance and anxiety](https://link.springer.com/article/10.1007/s00779-025-01846-8)
- [Project Aria Client SDK platform support](https://facebookresearch.github.io/projectaria_tools/docs/ARK/sdk/setup)
