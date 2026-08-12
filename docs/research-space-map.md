# VR Based Storytelling using ML — Research Space Map

**Status:** pre-design. Nothing here is a protocol. Purpose is to make the ambiguity explicit so you and your mentor can pick the actual research question.

**Date:** 2026-08-11
**Inputs:** mentor brief (title, rationale paragraph, 3-condition procedure, "storytelling is the medium"), V5.1 engineering abstract (`v5_1.md`), Aria Gen 2 public specs, adjacent literature.

---

## 0. The single most important reframe

The mentor's rationale paragraph contains this clause:

> "Aria enables the transition **from** controlled VR-based physiological storytelling research **to** scalable real-world environments, preserving immersion while allowing ecologically valid performance."

Read literally, **VR is the thing being left behind, not the thing being built.** The lab (or the literature the lab draws on) previously did storytelling + physiology studies inside VR headsets, in a lab, wired to sensors. Aria Gen 2 is being proposed as the replacement: same constructs, no headset, no lab, real environments.

If that reading is right:

- The project title "VR Based Storytelling using ML" is **legacy framing / grant language**, not a spec. There may be no VR headset in the study at all.
- "Preserving immersion" then means *preserving the psychological engagement that VR gave you*, using narrative instead of a headset. Storytelling is the immersion mechanism replacing VR.
- The novelty claim is **methodological**: can unobtrusive glasses recover the constructs that previously needed a lab rig?

If that reading is wrong, there is a real VR component (a headset showing a scene, Aria worn under/over it, or Aria data driving a VR reconstruction) and the design is completely different.

**This is question #1 for the mentor and it changes everything downstream.** Do not resolve it by assumption.

---

## PART A — WHAT WE ACTUALLY KNOW

Facts, not inference.

### A1. From the mentor, stated explicitly

| # | Known |
|---|---|
| K1 | Hardware is Meta Aria Gen 2. Not optional, not substitutable. |
| K2 | There will be **human participants** and **data collection** against defined groups. |
| K3 | There are exactly three named conditions: (1) first-person storytelling **with** Aria, (2) first-person storytelling **without** Aria, (3) **no** storytelling **with** Aria. |
| K4 | "Storytelling will be the medium." Medium — i.e. the vehicle through which something else is studied, not necessarily the object of study. |
| K5 | Existing code must be made to run with the glasses. Engineering is a prerequisite, not the contribution. |
| K6 | The psychological constructs named are **valence, arousal, dominance, and regulation**. |
| K7 | The named signal→construct bridges are: **gaze dispersion**, **prosody**, **micro-motion patterns**, and (truncated in your copy) something ending "...tual scene analysis" — almost certainly **contextual scene analysis** or **visual scene analysis**. |
| K8 | The claimed advantage is **non-interference with natural behavior** and **ecological validity**. |
| K9 | The word used is "approximate" — "approximate psychological constructs." Mentor is not claiming direct measurement. |

### A2. From the hardware (verified against Meta/Project Aria docs)

Aria Gen 2 sensor suite:

| Sensor | Notes |
|---|---|
| 1× RGB camera | egocentric scene |
| 4× SLAM / CV cameras | 6DOF, wide FOV, spatial understanding |
| 2× eye-tracking cameras | gaze estimation, on-device ET; in the egoEMOTION dataset these ran 640×480 @ 90 fps per eye |
| IMU (multiple), magnetometer, barometer | head micro-motion, posture, orientation; IMUs at 800–1000 Hz |
| GNSS (L1) | outdoor location |
| Spatial microphone array | scene audio, spatial |
| **PPG sensor (nosepad)** | **heart rate — a real physiological channel, ~128 Hz in published use** |
| **Contact microphone (nosepad)** | **isolates wearer's own voice from bystanders — the single best feature for a storytelling study** |
| On-device machine perception | location/VIO, hand tracking, eye tracking, ASR |
| Form factor | ~75 g, 6–8 h runtime, foldable |

Three consequences you should internalize:

1. **The PPG is what makes the mentor's paragraph honest.** Without it, "physiological storytelling research" on glasses is a stretch. With it, you have HR and potentially HRV — the same family of measures the VR lab studies used.
2. **The contact microphone is purpose-built for your task.** A storytelling study lives or dies on cleanly segmenting *the participant's speech* from the experimenter's, the room's, and bystanders'. Gen 2 solves this in hardware.
3. **Your V5.1 uses almost none of this.** V5.1 covers RGB + audio + transcription + LLM Q&A + session logging. Eye tracking, PPG, and contact mic — the three highest-value channels for the stated constructs — are not in the abstract you gave me.

### A3. From the V5.1 abstract

What exists: Aria connection/auth, RGB stream, audio stream (multichannel), transcription (OpenAI STT), LLM Q&A, wake/VAD experiments, synchronized recording, participant ID, data logging, configurable recording modes, an analysis stack (pandas/NumPy/matplotlib).

What that is: **a working instrument and a working interaction loop.** That is genuinely the hard, boring 60% of any wearable study.

What it is not: a study, a labelling scheme, a hypothesis, or a feature pipeline for the four named constructs.

### A4. Nearest prior work — read this before you talk to your mentor

**egoEMOTION** (arXiv 2510.22129) — Project Aria glasses, 43 participants (ages 19–29), ~50 hours. Signals: eye/periocular video 90 fps, egocentric RGB 10 fps, head IMU, **nosepad PPG 128 Hz**, plus reference wearables (chest ECG, finger PPG/EDA, respiration). Labels: 7-point emoji-SAM **valence, arousal, dominance**, 9 discrete emotion tags, Big Five. Tasks: 9 emotion-eliciting video clips + 7 naturalistic activities. Baselines: SVM F1 0.75 on binary V-A-D, RF F1 0.46 on 9-class emotion, RF 0.59 on Big Five. **Finding: eye-tracking features were the most informative modality, and egocentric signals beat traditional physiological baselines.**

Why this matters to you, bluntly:

- "Aria sensors → VAD" as a standalone contribution is **already published, with a public dataset, at N=43.** You will not beat it with a student-scale sample.
- But egoEMOTION used **passive video watching and casual activities**. It did **not** study *narrative production*, did **not** include a *no-device* control, and did **not** touch *regulation*.
- So the three things that survive as novel in your brief are exactly: **storytelling as an active production task**, **the with-Aria vs without-Aria device-reactivity contrast**, and **regulation**.
- Practical gift: their result tells you eye tracking is the highest-yield channel. That is a strong argument for prioritising ET in V6 over more RGB work.

**Other relevant grounding:**
- Gaze entropy literature: gaze dispersion *decreases* under load ("visual tunneling"); stationary gaze entropy and gaze transition entropy are the two standard operationalisations. So "gaze dispersion" in the mentor's paragraph has an established formal definition — use theirs, don't invent one.
- Expressive writing / disclosure paradigm (Pennebaker): participants who narrate emotionally significant personal events show measurable psychological and physical outcomes vs neutral-topic controls. Classic design is 15–20 min per session, 3–5 sessions, with a **neutral-topic control condition**. Your condition 3 ("no storytelling with Aria") is structurally the same slot as Pennebaker's neutral-topic control.
- Observer/reactivity literature: presence of recording technology (camera, drone, **smart glasses**) measurably raises anxiety vs no-observer. This is direct empirical support that your with-Aria vs without-Aria contrast is a real, publishable effect and not a formality.

---

## PART B — WHAT WE DON'T KNOW

Ranked by how much damage the wrong assumption does.

### B1. Blocking unknowns (cannot collect data without answers)

| # | Unknown | Why blocking |
|---|---|---|
| U1 | **Is there real VR, or is Aria replacing VR?** | Determines whether you need a headset, a virtual scene, and a whole second stack. |
| U2 | **Who tells the story — participant, experimenter, or the machine?** | "First-person storytelling" is genuinely ambiguous. Production vs reception are opposite studies with opposite signal profiles. |
| U3 | **Between-subjects or within-subjects?** | Mentor wrote "groups", which reads between-subjects. Within-subjects gives you a per-person baseline and roughly triples effective statistical power at the same N. This is the highest-leverage single design decision. |
| U4 | **What is measured in condition 2 (no Aria)?** | If nothing is measured, condition 2 produces zero data and cannot support any comparison. Needs an explicit answer: questionnaires only? external camera? consumer wearable? |
| U5 | **Where do labels come from?** | No labels, no supervised ML. Nobody has specified this. |
| U6 | **IRB / ethics status.** | Video + audio + eye images + heart rate + bystanders. Also Meta's own Project Aria research-use and bystander-privacy obligations. This has a lead time measured in weeks-to-months and is the most common cause of a stalled student study. |
| U7 | **N, and who the participants are.** | N=12 and N=120 are different projects. N determines whether the ML task is deep learning, classical ML, or descriptive statistics with no ML at all. |

### B2. Design unknowns

| # | Unknown |
|---|---|
| U8 | Is the story **content controlled** (everyone tells the same prompt) or **free** (personal event)? Controlled = comparable across participants, weaker affect. Free = strong affect, poor comparability. |
| U9 | Is there an **audience**? Telling a story to a person, to a camera, and to an empty room produce different prosody, gaze, and arousal. |
| U10 | Is the **LLM Q&A loop from V5.1 part of the study**, or leftover engineering? If it's in, the system is an interactive interlocutor and that's a confound *and* possibly the real contribution. |
| U11 | What does **"regulation"** mean here — trait (ERQ questionnaire), outcome (pre→post affect change), or moment-to-moment process? It is *not* a circumplex dimension, so it doesn't belong with V-A-D unless the mentor means something specific. |
| U12 | Session structure: single session or repeated (Pennebaker uses 3–5)? |
| U13 | What is the **fourth missing cell** — "no storytelling, no Aria"? Its absence means the design cannot fully separate device effects from task effects. Was that deliberate or an oversight? |
| U14 | Is the target an **artifact** (a working system), a **finding** (a claim about people), or a **dataset**? |

### B3. Technical unknowns

| # | Unknown |
|---|---|
| U15 | Does your Gen 2 unit + current SDK actually stream **eye tracking** and **PPG** live, or only record to device for later extraction? V5.1 does not demonstrate either. |
| U16 | Contact-mic accessibility from the SDK. |
| U17 | Cross-stream time synchronisation quality (you have "synchronized recording infrastructure" — how good, measured how?). |
| U18 | Storage/bandwidth for full multimodal capture × N participants × session length. |
| U19 | Is the OpenAI dependency (STT + LLM) acceptable for participant data under your IRB? Sending participant speech to a third-party API is an ethics-form question, not just an engineering one. |

---

## PART C — SEVEN PLAUSIBLE INTERPRETATIONS

Each is internally consistent with the mentor's brief. They are not all equally likely; likelihood is my estimate, stated as such.

---

### Interpretation 1 — "Can glasses replace the lab?" (instrument validation)
*Likelihood: high*

**Claim under test:** Aria Gen 2 recovers the affective/physiological signals that previously required a VR lab rig, without changing behaviour.

Storytelling is a *reliable affect elicitor* — nothing more. The science is about the instrument. Condition 2 (no Aria) is the crux: it's the control that proves non-interference. Condition 3 (no story) is the resting/neutral baseline.

**Fits:** K8 (non-interference), K9 ("approximate"), the whole "transition from VR to real-world" sentence, and the missing 4th cell (you don't need it if the device, not the task, is the object of study).
**ML task:** signal→construct regression, but the headline result is a *comparison*, not a classifier.
**Risk:** proving a null (no device effect) needs equivalence testing and decent N.

---

### Interpretation 2 — "Narrative as emotion regulation" (psychology study)
*Likelihood: high*

**Claim under test:** Telling a first-person story about an emotional event changes affective state; Aria captures the trajectory.

This is the Pennebaker disclosure paradigm ported to speech and instrumented with glasses. "First-person" = *about the participant's own life*. Condition 3 = the neutral-topic control. "Regulation" is the outcome variable — that's why it's in the construct list next to V-A-D.

**Fits:** K4 ("medium"), K6 (regulation), "first person".
**ML task:** secondary — predict pre→post affect change, or detect regulation events in the narrative.
**Risk:** this is a psychology paper with an ML appendix. Check that's acceptable.

---

### Interpretation 3 — "Multimodal affect recognition during narrative production"
*Likelihood: medium-high, and the one you were warned not to lock onto*

**Claim under test:** From gaze + prosody + micro-motion + scene, predict VAD during storytelling.

The straightforward affective-computing read. Condition 3 supplies negative/neutral class data; condition 2 is barely used.

**Fits:** K7 (the signal list is literally a feature list), K6.
**ML task:** regression/classification on VAD.
**Risk:** **this is egoEMOTION's exact task, already done at N=43 with better instrumentation than you'll have.** Only defensible as a *narrative-specific* variant, or with the device-reactivity contrast attached.

---

### Interpretation 4 — "Machine as storyteller / story-generator from egocentric experience"
*Likelihood: low-medium*

**Claim under test:** The system generates or co-constructs narrative from what the wearer saw and said.

Reads the title as "storytelling *using* ML" — ML is the author. V5.1's transcription + LLM Q&A loop is the seed. Aria gives grounded episodic material (scene, gaze, location, speech); the LLM turns it into narrative.

**Fits:** the title's literal grammar, the LLM in V5.1, "contextual scene analysis".
**Against:** does not explain the three conditions or the psychological constructs at all.
**ML task:** grounded narrative generation, evaluated on coherence/groundedness/human preference.
**Risk:** if this is it, the human-participant conditions are a *separate* evaluation study, and half the mentor's paragraph is decoration.

---

### Interpretation 5 — "Immersion / presence transfer" (VR construct without VR)
*Likelihood: medium*

**Claim under test:** Narrative produces measurable immersion/presence in the real world, comparable to what VR produces, and Aria detects it.

Anchors on "**preserving immersion** while allowing ecologically valid performance." Presence is *the* VR construct. The claim is that story does what the headset used to.

**Fits:** the immersion clause, the VR lineage, gaze dispersion (attentional narrowing = engagement).
**ML task:** predict presence/engagement scores from gaze entropy + micro-motion.
**Risk:** presence questionnaires designed for VR may not transfer to a real-room narrative task.

---

### Interpretation 6 — "Observer effect / device reactivity" (methods study)
*Likelihood: medium — and the sharpest small-N option*

**Claim under test:** Wearing sensing glasses changes how people tell personal stories.

Inverts Interpretation 1: the device is the *independent variable*, not the instrument. Condition 1 vs 2 is the whole study. The literature already shows recording technology raises anxiety; nobody has shown it specifically for *narrative self-disclosure*, which is where it matters most, because disclosure depth is privacy-sensitive by definition.

**Fits:** the with/without-Aria pair, K8 read as a *hypothesis to test* rather than an assumption.
**Data:** condition 2 must be measured by non-Aria means — this interpretation forces U4 to be answered.
**ML task:** minimal. Possibly "classify condition from transcript/prosody" as an effect-size demonstration.
**Risk:** thin on ML. Strong on publishability and honesty.

---

### Interpretation 7 — "Build the dataset and the pipeline"
*Likelihood: medium — and possibly what your mentor actually needs from you this term*

**Claim under test:** none. Deliverable is a synchronised multimodal storytelling corpus + reproducible feature pipeline + baselines.

"We have to use the code and make it run with the glasses" is the most concrete, least ambiguous sentence in the brief. It may be the actual assignment.

**Fits:** K5, V5.1's trajectory, the vagueness everywhere else.
**ML task:** baselines only, deliberately.
**Risk:** you need to know if this is the goal, because it changes what "success" means. Building a corpus and calling it a contribution is legitimate — but only if agreed in advance.

---

## PART D — THE MAJOR RESEARCH DECISIONS

Six forks. Everything else follows.

### D1. Is the device the instrument or the variable?
- **Instrument** → Aria measures storytelling. Analysis is within condition 1 vs 3.
- **Variable** → Aria's presence perturbs storytelling. Analysis is condition 1 vs 2.
- You can attempt both, but they have opposite power requirements and opposite framings, and only one can be the headline.

### D2. Storytelling — production or reception?
- **Production** (participant speaks): rich prosody, own-voice audio via contact mic, gaze on listener/room, self-generated content, hard to standardise.
- **Reception** (participant listens/watches): standardised stimulus, gaze on the stimulus, comparable across people, weaker and more passive signal.
- "First-person" tilts hard toward production. Confirm anyway.

### D3. Within-subjects or between-subjects?
Decode the 3 conditions as a 2×2 with one empty cell:

|  | **Aria worn** | **No Aria** |
|---|---|---|
| **Storytelling** | C1 | C2 |
| **No storytelling** | C3 | *(missing)* |

- **C1 vs C3** — effect of storytelling, both measured by Aria. This is where your ML labels come from.
- **C1 vs C2** — effect of the device on storytelling. Requires non-Aria measurement.
- **Missing cell** — without it you cannot estimate the device × task interaction.
- **Within-subjects** (every participant does all three, order counterbalanced): per-person baseline, removes between-person physiological variation (which is huge for HR and gaze), far better at small N. Cost: carryover, fatigue, and you can't un-know that you wore the glasses.
- **Between-subjects**: clean, no carryover, needs roughly 3× the participants.

**Recommendation to raise with your mentor: within-subjects, counterbalanced, unless there's a specific reason not to.** At student N, between-subjects will likely find nothing.

### D4. Where do labels come from?
| Source | Gives you | Cost | Trap |
|---|---|---|---|
| Post-condition SAM (valence/arousal/dominance, 7-pt) | 1 label per condition per person | trivial | ~3 labels/person total — too few for ML |
| Per-segment SAM (every 60–90 s) | 10–30 labels/person | interrupts the narrative | breaks immersion, the thing you're preserving |
| Continuous annotation dial, retrospective while re-watching own recording | dense time-series | ~1× session duration extra per participant | recall bias; but this is the standard solution |
| Third-party annotators rating the recording | dense, no participant burden | annotator hours, IRR | measures *perceived* affect, not felt affect — different construct, say so |
| LLM scoring the transcript | free, dense | none | **circular** if you then predict it from audio. Only defensible as a text-only reference channel |
| Condition ID as label | free, perfectly clean | none | you learn "did they talk", not "how did they feel" |
| PPG-derived HR/HRV as arousal proxy | free, dense, continuous | none | proxy, not ground truth — must be validated against self-report, not substituted for it |

**The realistic answer for a student study is a combination: per-condition SAM + retrospective continuous annotation on a subset + PPG as a physiological reference.** Decide this *before* collection. Labels cannot be retrofitted onto sessions you already ran.

### D5. Which sensors do you actually commit to?
Ranked by value-per-engineering-hour for the stated constructs:

1. **Eye tracking** — highest. It's the named construct (gaze dispersion), it has a formal operationalisation (SGE/GTE), and egoEMOTION found it the most informative modality. Not in V5.1.
2. **Contact microphone** — near-free win. Solves own-voice segmentation, which every prosody feature depends on. Not in V5.1.
3. **PPG** — the physiological channel that makes the mentor's whole framing defensible. Not in V5.1.
4. **IMU** — micro-motion; you likely have some already.
5. **Audio (spatial array)** — prosody: F0, jitter, shimmer, energy, pause structure, speech rate. Have it.
6. **RGB / SLAM** — contextual scene analysis. Have RGB. Highest storage cost, least direct link to affect. Deprioritise.

**This ranking is roughly inverted from where V5.1's effort has gone.** That's not a criticism of V5.1 — connection and sync had to come first — but V6 should go up the list, not sideways.

### D6. Is the deliverable a system, a finding, or a dataset?
Ask directly. Grading, timeline, and scope all hang on it.

---

## PART E — QUESTIONS FOR THE MENTOR AND THE CONSEQUENCES OF EACH ANSWER

### Q: Is there an actual VR headset, or is Aria replacing VR?
| Answer | Consequence |
|---|---|
| Aria replaces VR | Title is legacy. No headset. Full ecological-validity framing. **Most likely.** |
| Both — Aria worn in VR | Massive scope increase: headset compatibility, VR content, gaze from two sources. Verify Aria can even be worn with the target headset before agreeing. |
| VR reconstructed *from* Aria data | Different project entirely: 3D scene reconstruction + narrative replay. Interpretation 4 territory. |

### Q: Who tells the story?
| Answer | Consequence |
|---|---|
| Participant | Production study. Contact mic + prosody become primary. Content standardisation problem (D2). |
| Experimenter/recording, participant listens | Reception study. Gaze on stimulus. Standardised. Weaker signal. |
| System/LLM generates it | Interpretation 4. The three conditions need re-explaining. |

### Q: Same participant does all three, or three separate groups?
| Answer | Consequence |
|---|---|
| Within | Paired stats, per-person baselines, viable at N≈15–25. Needs counterbalancing + washout. |
| Between | Needs N≈60–90+ for modest effects. At student N you will likely report a null you can't interpret. |

### Q: In condition 2 (no Aria), what do we measure?
| Answer | Consequence |
|---|---|
| Nothing / questionnaires only | Condition 2 supports only self-report comparison. No signal-level analysis. State this limitation up front. |
| External camera + room mic | Enables prosody and coarse motion comparison. Adds a sync problem and a second ethics item. |
| Consumer wearable (chest strap / wrist) | Enables HR comparison vs Aria PPG — and doubles as PPG validation. Cheap, high value. **Best answer.** |
| Aria worn but not recording | Then it isn't a no-device condition; it's a *belief* manipulation. Interesting, but a different study — and it involves deceiving participants, which is an IRB issue. |

### Q: What does "regulation" mean?
| Answer | Consequence |
|---|---|
| Trait (ERQ questionnaire) | One-time covariate. Cheap. Enables "do reappraisers show different gaze patterns" analyses. |
| Outcome (pre→post affect change) | Needs pre/post PANAS or SAM. This is the Pennebaker read. Cheap and high value. |
| Moment-to-moment process | Hardest. Needs dense annotation and a coding scheme for regulation events in speech. Probably out of scope. |

### Q: Are eye tracking and PPG in scope?
| Answer | Consequence |
|---|---|
| Yes | V6 engineering priority is clear. Verify SDK streaming support **this week** — before you promise anything. |
| No, RGB + audio only | Then "gaze dispersion" must be dropped from the framing, and you should say so explicitly, because it's in the mentor's own paragraph. Half the stated construct bridges disappear. |

### Q: What N, and what timeline?
| Answer | Consequence |
|---|---|
| N < 15 | No ML beyond descriptive baselines. Frame as feasibility/pilot. That is a legitimate output — but agree on it now. |
| N ≈ 20–40 | Classical ML on hand-engineered features, subject-wise cross-validation, no deep learning. |
| N > 60 | Learned representations become defensible. Unlikely for one term. |

### Q: Is IRB approved, submitted, or not started?
| Answer | Consequence |
|---|---|
| Approved | Read it. Your design must fit *it*, not the other way round. |
| Submitted | Find out what was promised — it constrains everything. |
| Not started | **This is your critical path, not the code.** Start now. Include: bystander privacy, eye-image and biometric data handling, third-party API transmission of participant speech (the OpenAI dependency in V5.1), and data retention. |

### Q: Is the LLM Q&A loop part of the study?
| Answer | Consequence |
|---|---|
| Yes, it's the interlocutor | Then the system is a conversational partner and its behaviour is a variable that must be controlled or logged exhaustively. Possibly the actual contribution. |
| No, leftover | Turn it off during sessions. An LLM improvising responses mid-story is an uncontrolled confound. |

### Q: Do you know about egoEMOTION?
| Answer | Consequence |
|---|---|
| Yes | Good — ask what they see as the delta. Likely: narrative production, the no-device control, regulation. |
| No | Bring it. It's Aria + PPG + eye tracking + VAD at N=43, published. It reshapes what counts as novel here, and it hands you a modality-priority result for free. |

---

## PART F — DECISION TREE

Format: **MENTOR ANSWER → INTERPRETATION → STUDY DESIGN → DATA → LABELS → ANALYSIS → ML TASK**

---

### Branch 1 — "Aria replaces VR; we're validating the instrument"
- **Interpretation:** 1 (instrument validation), with 6 attached
- **Design:** within-subjects, 3 conditions counterbalanced; add a consumer HR strap in all three so condition 2 isn't blind
- **Data:** Aria full stack (ET, PPG, IMU, contact mic, audio, RGB) in C1/C3; strap + room audio + questionnaires in C2
- **Labels:** SAM per condition; ERQ once; retrospective continuous annotation on a subset
- **Analysis:** Aria PPG vs chest strap agreement (Bland–Altman); C1 vs C2 equivalence tests on self-report and prosody; C1 vs C3 for storytelling effects
- **ML:** regression from Aria features → self-reported VAD, subject-wise CV; report against an egoEMOTION-style baseline. **Secondary to the validation result.**

### Branch 2 — "Participant tells a personal story; we care about regulation"
- **Interpretation:** 2 (disclosure paradigm)
- **Design:** within-subjects; C1 = personal emotional event, C3 = neutral topic (describe your route to campus), C2 = personal event without glasses; pre/post affect each condition
- **Data:** contact mic + audio primary; ET + PPG for arousal trajectory; IMU secondary; RGB minimal
- **Labels:** pre/post PANAS + SAM; ERQ; optional LIWC-style or LLM text analysis of the transcript as an independent channel
- **Analysis:** pre→post affect change by condition; arousal trajectory over narrative time; does disclosure depth differ with vs without glasses
- **ML:** predict pre→post change from early-session features; or detect high- vs low-disclosure segments

### Branch 3 — "Predict affect from sensors during storytelling"
- **Interpretation:** 3
- **Design:** maximise labelled minutes per participant; C3 supplies neutral/low-arousal data; C2 largely unused
- **Data:** ET (SGE + GTE, blink rate, pupil if available), prosody (F0 stats, jitter, shimmer, energy, speech rate, pause distribution), IMU micro-motion (spectral band power, stillness ratio), PPG (HR, HRV), RGB scene features
- **Labels:** retrospective continuous annotation is **mandatory** here — per-condition SAM gives you ~3 labels/person and that is not a dataset
- **Analysis:** feature-level correlation with annotation; ablation by modality
- **ML:** continuous VAD regression (CCC metric, as in the affect-recognition literature), subject-wise CV. **Must be positioned against egoEMOTION or a reviewer will do it for you.**

### Branch 4 — "The system generates the story"
- **Interpretation:** 4
- **Design:** participants wear Aria through an activity; system generates a narrative; participants rate it. The 3-condition structure becomes an evaluation design, not an experimental one
- **Data:** RGB + ASR + location + gaze-as-salience
- **Labels:** human ratings of coherence, groundedness, personal resonance
- **Analysis:** ablation — does gaze-based salience improve the generated narrative over RGB alone?
- **ML:** grounded narrative generation; gaze as an attention prior for what to include

### Branch 5 — "Immersion without the headset"
- **Interpretation:** 5
- **Design:** within-subjects; presence/engagement questionnaire after each condition
- **Data:** ET (dispersion/tunneling), IMU (stillness), PPG
- **Labels:** presence + narrative-engagement scales
- **Analysis:** does gaze entropy drop during high-engagement narrative segments
- **ML:** predict engagement score from gaze entropy + micro-motion. Small, clean, achievable.

### Branch 6 — "Do the glasses change the story?"
- **Interpretation:** 6
- **Design:** **C1 vs C2 is the entire study.** Add the missing 4th cell if N allows — it converts this into a clean 2×2
- **Data:** matched non-Aria capture (external mic minimum) so the two conditions are comparable at signal level
- **Labels:** self-reported comfort, self-consciousness, disclosure depth; blind third-party ratings of narrative openness
- **Analysis:** paired comparison of disclosure depth, word count, pause structure, self-referential language, emotional word use
- **ML:** thin by design — "can a classifier tell which condition a transcript came from" as an effect-size demonstration
- **Honest note:** the least ML-heavy branch and possibly the most publishable at student N.

### Branch 7 — "Build the corpus and the pipeline"
- **Interpretation:** 7
- **Design:** whatever maximises data quality and diversity
- **Data:** everything, fully synchronised, documented
- **Labels:** the richest set you can afford — future users can't add them later
- **Analysis:** sync quality, data completeness, sensor dropout rates
- **ML:** published baselines only
- **Note:** legitimate contribution, but only if agreed in advance. Do not discover in month 5 that this was what was wanted.

---

## THE 10 QUESTIONS I SHOULD ASK MY MENTOR BEFORE WE COLLECT PARTICIPANT DATA

Ask in this order. First four are blocking.

1. **"Is there an actual VR headset in this study, or is Aria replacing the VR setup that earlier studies used?"**

2. **"In 'first-person storytelling', who is speaking — the participant telling their own story, or the participant listening to one?"**

3. **"Does each participant do all three conditions, or is each condition a separate group of people? And roughly how many participants are we planning?"**

4. **"What's the IRB status? Is it approved, submitted, or do I need to help write it?"** *(Follow up: does it cover eye images, heart rate, bystanders, and sending participant speech to the OpenAI API?)*

5. **"In the 'without Aria' condition, what are we actually measuring? Just questionnaires, or should I set up an external recorder or a heart-rate strap?"**

6. **"How will we know what someone was feeling? Do participants rate themselves, do we annotate the recordings afterward, or something else?"** *(This is the labels question, phrased so it can't be waved off.)*

7. **"When you wrote 'regulation' alongside valence, arousal, and dominance — do you mean a trait we measure once with a questionnaire, or a change from before to after the session?"**

8. **"Are eye tracking and the nosepad PPG heart-rate sensor in scope? Right now the system does RGB and audio, and adding those two is where I'd put my next engineering effort — is that the right priority?"**

9. **"Is the goal a working system, a finding about people, or a dataset other people can use? What would 'done' look like at the end of the term?"**

10. **"Have you seen egoEMOTION? It's Aria glasses, 43 participants, eye tracking plus nosepad PPG, with valence-arousal-dominance labels. What do you see as the difference between that and what we're doing?"**

**Bonus, if there's time:** *"Should the LLM question-and-answer part be running during the sessions, or turned off?"*

---

## MY CURRENT UNDERSTANDING — ONE PARAGRAPH

My current best reading — and it is a reading, not a settled fact — is that this project is probably **not** primarily an emotion-recognition problem, and probably **not** actually about VR. The mentor's own sentence positions Aria Gen 2 as the *successor* to VR-based physiological storytelling research, which suggests the title is inherited framing and the real question is methodological: whether unobtrusive glasses can recover, in a real room, the affective and physiological constructs that previously required a lab and a headset — with first-person storytelling serving as a reliable and ecologically natural way to move those constructs around ("storytelling will be the medium"). Under that reading, the three conditions decode as a 2×2 with one cell missing, where *storytelling with Aria* versus *no storytelling with Aria* isolates the effect of narrative, and *storytelling with Aria* versus *storytelling without Aria* tests whether the device itself perturbs the behaviour it claims not to interfere with — a contrast that only means anything if we decide what gets measured in the no-glasses condition, which nobody has specified yet. I am genuinely unsure whether "first-person storytelling" means the participant produces a narrative or receives one, whether the design is within- or between-subjects, and above all where the affect labels come from, since the sensor pipeline is well advanced while the labelling scheme does not appear to exist — and labels cannot be added to sessions after they are recorded. I also can't yet tell whether the intended deliverable is a system, a finding, or a corpus, and the existence of egoEMOTION (Aria, 43 participants, eye tracking and nosepad PPG, valence-arousal-dominance labels, published baselines) means that the plainest ML reading of this brief is already occupied, so the defensible novelty most likely lives in narrative *production*, in the no-device control, or in "regulation" — none of which egoEMOTION touched. Everything above should be treated as hypotheses to test against my mentor in conversation, not conclusions to build on.

---

## APPENDIX — SUGGESTED IMMEDIATE ACTIONS (independent of which branch wins)

These are safe under every interpretation, so they don't have to wait for the mentor meeting:

1. **Verify eye-tracking and PPG streaming on your actual unit and SDK version.** If they don't stream live, find out whether they at least record to device for offline extraction. Everything in the mentor's construct list depends on the answer, and it's a one-afternoon check.
2. **Verify the contact microphone is accessible.** It's the cheapest large win in the whole stack.
3. **Measure your cross-stream sync**, don't assert it. Clap/flash test, report the residual in milliseconds. Every multimodal claim you make later rests on this number.
4. **Start the IRB paperwork.** Longest lead time, zero dependency on the research question.
5. **Run one pilot on yourself, end to end** — consent through analysis — and count exactly how many minutes of usable, labelled data one session yields. That number, multiplied by your realistic N, tells you which branches in Part F are actually reachable.
6. **Read egoEMOTION properly** (arXiv 2510.22129), especially their feature set and their subject-wise evaluation protocol. Free experimental design, and it tells you eye tracking is worth more than RGB.

---

## SOURCES

- [Aria Gen 2 Glasses — Project Aria](https://www.projectaria.com/glasses/)
- [Introducing Aria Gen 2 — Meta](https://www.meta.com/blog/project-aria-gen-2-next-generation-egocentric-research-glasses-reality-labs-ai-robotics/)
- [Inside Aria Gen 2: under the hood — Meta AI](https://ai.meta.com/blog/aria-gen-2-research-glasses-under-the-hood-reality-labs/)
- [Aria Gen 2 Documentation](https://facebookresearch.github.io/projectaria_tools/gen2/)
- [projectaria_tools (GitHub)](https://github.com/facebookresearch/projectaria_tools)
- [projectaria-client-sdk (PyPI)](https://pypi.org/project/projectaria-client-sdk/)
- [egoEMOTION: Egocentric Vision and Physiological Signals for Emotion and Personality Recognition](https://arxiv.org/html/2510.22129)
- [Aria Gen 2 Pilot Dataset](https://www.projectaria.com/datasets/gen2pilot/)
- [Gaze entropy metrics for mental workload estimation](https://www.sciencedirect.com/science/article/abs/pii/S0001457524001052)
- [Gaze transition entropy as a measure of attention allocation](https://pmc.ncbi.nlm.nih.gov/articles/PMC11461703/)
- [Emotional and physical health benefits of expressive writing (Baikie & Wilhelm)](https://sparq.stanford.edu/sites/g/files/sbiybj19021/files/media/file/baikie_wilhelm_2005_-_emotional_and_physical_health_benefits_of_expressive_writing.pdf)
- [Pennebaker & Chung — Expressive Writing, Emotional Upheavals, and Health](https://c3po.media.mit.edu/wp-content/uploads/sites/45/2016/01/PennebakerChung_FriedmanChapter.pdf)
- [Efficacy of expressive writing: systematic review and meta-analysis](https://pmc.ncbi.nlm.nih.gov/articles/PMC10415981/)
- [Affective stance and psychophysiological responses during conversational storytelling](https://www.sciencedirect.com/science/article/abs/pii/S0378216614000812)
- [Under the camera eye: effects of video-surveillance technology on users' performance and anxiety](https://link.springer.com/article/10.1007/s00779-025-01846-8)
- [Mind the Gap: Wearer–Bystander Privacy Tensions for Camera Glasses (CHI 2026)](https://dl.acm.org/doi/10.1145/3772318.3791848)
