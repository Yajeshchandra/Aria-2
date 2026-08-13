# egoEMOTION — Paper Summary with Evidence

**Full title:** egoEMOTION: Egocentric Vision and Physiological Signals for Emotion and Personality Recognition in Real-World Tasks
**arXiv:** 2510.22129
**Local copy:** `docs/egoEmotion.pdf` (25 pages)

**Why this paper matters here:** it is the closest existing work to this project — same glasses, same sensors, overlapping constructs. It defines what is already known, what cannot be claimed as novel, and which modalities are worth engineering effort.

> **Provenance note.** The numbers below were extracted from the HTML edition at `arxiv.org/html/2510.22129v1`, because PDF page rendering is unavailable in this environment (poppler not installed). Tables are reproduced in full so any figure can be checked against the local PDF. **Spot-check a few before quoting them in a submitted document.**

---

## 1. TL;DR

Aria glasses alone read affect better than a full chest-and-finger physiological rig. Classical machine learning beat deep learning at N = 43. Eye-derived features and head motion carried the signal; the nosepad PPG was at chance for discrete emotion. Nobody analysed audio, nobody ran a no-device control, and the authors themselves flag sparse coverage of the low-arousal-negative region.

---

## 2. What they did

**Participants:** 43 (24 female, 19 male), ages 19–29. ~50 hours total. Office room, experimenter behind a curtain.

**Two sessions per participant:**

*Session A — induced emotion (~20 min).* Nine video clips of ~48 s each, targeting eight emotions from Mikels' Wheel plus neutral. Loop per clip:
```
5 s fixation cross      → recalibrates gaze tracking
clip (~48 s)
two self-report questionnaires
neutral "cloud" video   → washes out carryover
```

*Session B — naturalistic activities (~49 min).* Seven tasks, order randomised per participant:

| Task | Duration | Target |
|---|---|---|
| Flappy Bird | 4 min | frustration |
| Jelly Bean | 2 min | disgust (unpleasant tastes) |
| Jenga | 5 min | played with experimenter |
| Painting | 4 min | creative, with music |
| Sad Letter | 4 min | writing, classical music |
| Slenderman | 6 min | fear (horror game) |
| Try to Laugh | 4 min | joke exchange |

**Labels — collected after every one of the 16 tasks:**
- emoti-SAM, 7-point emoji scale: arousal, valence, dominance
- Weighted emotion tags: distribute 100% across nine emotions in 10% increments
- Big Five Inventory, completed online *before* the visit

**Sensors worn simultaneously:**

| Device | Streams |
|---|---|
| Meta Project Aria glasses | eye video 640×480 @ 90 fps per eye; POV RGB 1408×1408 @ 10 fps; head IMU 800 + 1000 Hz; nosepad PPG 128 Hz |
| Reference rig | chest ECG, respiratory belt, ear-mounted Shimmer3 PPG, finger EDA |
| External | face video 60 fps, 1280×720 |

---

## 3. Feature extraction

Almost every signal was reduced to **15 statistical descriptors** (mean, std, percentiles).

**From the eye-tracking video** — six separate families:

| Feature | Method |
|---|---|
| Pupil size | open-source eye-tracking algorithm → 15 descriptors |
| Pixel intensity | mean brightness per eye frame → 15 descriptors |
| Fisherface | PCA → LDA trained per target variable, projected to 1-D → 15 descriptors |
| Gaze | yaw/pitch from Meta's Project Aria gaze tool → 15 descriptors |
| Blink | variance mapping over eye frames → 15 descriptors |
| Micro-expression | LBP-TOP, 10-frame (~111 ms) windows, averaged |

**Physiological — 612 features total:** ECG and PPG 77 each, EDA 31, respiration 14, head acceleration magnitude 15.

**Models:** SVM-RBF for continuous affect (binary, median split of training data); Random Forest for discrete emotion and per-trait personality, with SelectKBest top-10 by mutual information. **Leave-one-subject-out cross-validation throughout.** Per-participant feature standardisation to [0,1]. **scikit-learn defaults, no hyperparameter tuning.**

---

## 4. Evidence — Table 3, full results (F1)

Best non-combined value in each row is what matters; `Random` is the chance baseline.

### 4.1 Continuous affect (binary V/A/D)

| | ECG | EDA | RSP | Pupil | Intens. | Fisher. | Gaze | Blink | MicroX | PPG | IMU | **All** | *Random* |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Arousal | 0.76 | 0.76 | 0.75 | 0.77 | 0.76 | 0.76 | 0.78 | 0.76 | 0.76 | 0.75 | 0.78 | **0.78** | *0.64* |
| Valence | 0.67 | 0.64 | 0.69 | 0.73 | 0.72 | 0.69 | 0.63 | 0.66 | 0.68 | 0.66 | 0.75 | **0.76** | *0.55* |
| Dominance | 0.63 | 0.66 | 0.66 | 0.67 | 0.66 | 0.65 | 0.65 | 0.69 | 0.66 | 0.67 | 0.67 | **0.68** | *0.57* |
| **Mean** | 0.69 | 0.69 | 0.70 | 0.72 | 0.71 | 0.70 | 0.69 | 0.70 | 0.69 | 0.70 | 0.72 | **0.75** | *0.59* |

Whole row spans 0.69–0.72. Spread is 0.03.

### 4.2 Discrete emotion (9-class)

| | ECG | EDA | RSP | Pupil | Intens. | Fisher. | Gaze | Blink | MicroX | PPG | IMU | **All** | *Random* |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Amused | 0.37 | 0.44 | 0.45 | 0.39 | 0.50 | 0.43 | 0.36 | 0.23 | 0.32 | 0.31 | 0.58 | 0.50 | *0.21* |
| Content | 0.28 | 0.20 | 0.29 | 0.37 | 0.49 | 0.31 | 0.31 | 0.23 | 0.20 | 0.20 | 0.54 | 0.52 | *0.16* |
| Excited | 0.00 | 0.05 | 0.00 | 0.10 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.12 | 0.12 | *0.05* |
| Awe | 0.00 | 0.00 | 0.00 | 0.24 | 0.00 | 0.00 | 0.06 | 0.05 | 0.00 | 0.00 | 0.23 | 0.31 | *0.04* |
| Neutral | 0.18 | 0.29 | 0.22 | 0.36 | 0.34 | 0.34 | 0.36 | 0.16 | 0.17 | 0.17 | 0.37 | 0.41 | *0.17* |
| Fear | 0.06 | 0.14 | 0.17 | 0.48 | 0.40 | 0.08 | 0.24 | 0.04 | 0.20 | 0.10 | 0.42 | 0.55 | *0.08* |
| Sad | 0.15 | 0.42 | 0.17 | 0.45 | 0.52 | 0.32 | 0.37 | 0.11 | 0.12 | 0.10 | 0.60 | 0.57 | *0.10* |
| Disgust | 0.08 | 0.40 | 0.27 | 0.40 | 0.61 | 0.34 | 0.40 | 0.08 | 0.20 | 0.18 | 0.60 | 0.65 | *0.12* |
| Anger | 0.03 | 0.05 | 0.11 | 0.26 | 0.17 | 0.17 | 0.12 | 0.09 | 0.03 | 0.00 | 0.48 | 0.53 | *0.08* |
| **Mean** | 0.13 | 0.22 | 0.19 | 0.34 | 0.34 | 0.22 | 0.25 | 0.11 | 0.14 | 0.12 | **0.44** | **0.46** | *0.11* |

Spread is 0.11 → 0.44, a 4× range. **ECG (0.13), PPG (0.12) and Blink (0.11) are at chance.**

### 4.3 Personality (Big Five, binary per trait)

| | ECG | EDA | RSP | Pupil | Intens. | Fisher. | Gaze | Blink | MicroX | PPG | IMU | **All** | *Random* |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Extraversion | 0.28 | 0.52 | 0.32 | 0.40 | 0.60 | 0.50 | 0.58 | 0.43 | 0.48 | 0.30 | 0.55 | 0.55 | *0.55* |
| Agreeableness | 0.38 | 0.42 | 0.48 | 0.45 | 0.40 | 0.60 | 0.60 | 0.35 | 0.43 | 0.40 | 0.57 | 0.30 | *0.52* |
| Conscientiousness | 0.55 | 0.55 | 0.30 | 0.55 | 0.65 | 0.45 | 0.48 | 0.58 | 0.55 | 0.57 | 0.40 | 0.55 | *0.55* |
| Negative Emotionality | 0.52 | 0.50 | 0.65 | 0.68 | 0.60 | 0.55 | 0.60 | 0.50 | 0.58 | 0.42 | 0.30 | 0.68 | *0.52* |
| Open-Mindedness | 0.32 | 0.55 | 0.50 | 0.48 | 0.30 | 0.62 | 0.53 | 0.38 | 0.33 | 0.60 | 0.57 | 0.70 | *0.52* |
| **Mean** | 0.41 | 0.51 | 0.45 | 0.51 | 0.51 | 0.54 | 0.56 | 0.45 | 0.47 | 0.46 | 0.48 | **0.59** | *0.53* |

Agreeableness with all modalities scores **0.30 against a 0.52 baseline — worse than chance.** Extraversion and Conscientiousness land exactly on chance. This benchmark did not work.

---

## 5. Evidence — Table 4, classical vs deep learning

| Benchmark | Method | Wearable devices | Egocentric glasses | All |
|---|---|---|---|---|
| **Continuous affect** | Classical | 0.70 ± 0.14 | **0.74 ± 0.13** | **0.75 ± 0.13** |
| | DCNN | 0.63 ± 0.05 | 0.68 ± 0.05 | 0.68 ± 0.07 |
| | Transformer | 0.49 ± 0.21 | 0.65 ± 0.11 | 0.60 ± 0.16 |
| **Discrete emotion** | Classical | 0.28 ± 0.08 | **0.52 ± 0.18** | 0.45 ± 0.17 |
| | DCNN | 0.12 ± 0.01 | 0.23 ± 0.03 | 0.22 ± 0.02 |
| | Transformer | 0.13 ± 0.02 | 0.22 ± 0.03 | 0.21 ± 0.04 |
| **Personality** | Classical | 0.50 ± 0.48 | 0.57 ± 0.49 | 0.59 ± 0.49 |
| | DCNN | 0.43 ± 0.26 | 0.42 ± 0.20 | 0.41 ± 0.25 |
| | Transformer | 0.38 ± 0.28 | 0.47 ± 0.24 | 0.44 ± 0.28 |

**Two facts to carry forward:**
1. **Glasses beat the reference rig.** 0.74 vs 0.70 on affect; 0.52 vs 0.28 on discrete emotion. Adding the rig on top of the glasses *hurt* discrete emotion (0.45 vs 0.52).
2. **Deep learning lost every benchmark.** Authors attribute it to dataset size relative to model capacity.

---

## 6. Stated limitations

Quoted or closely paraphrased from the paper:

- *"Ground truth labels rely on retrospective self-reports after each task, which may be affected by recall bias and do not capture the dynamic nature of emotional responses"*
- Limited representation in the **low-arousal / low-valence** emotional quadrant
- Participants *"primarily composed of young adults"* — demographic bias
- Eye and facial features extracted were minimal; emotion-specific features (narrowed eyes, teary eyes) not implemented
- Deep-learning underperformance attributed to limited dataset size

---

## 7. What this means for this project

### 7.1 Which column applies to you

| Your label type | Read this column | Consequence |
|---|---|---|
| SAM valence/arousal/dominance ratings | Continuous affect | Everything scores 0.69–0.72. Modality choice barely matters — combine everything. |
| Emotion category (sad / happy / neutral script targets) | Discrete emotion | 4× spread. Modality choice decides the result. |

### 7.2 Modality decisions

**Tier 1 — build these**

| Modality | Affect | Discrete | Status in V5.1 |
|---|---|---|---|
| Head IMU | 0.72 | **0.44** (best single) | Recorded, collapsed to one scalar for PPG gating |
| Pupil | 0.72 | 0.34 | Not extracted |
| Prosody / own-voice | — | — | Not recorded |

⚠️ Head motion during script reading partly encodes *reading mechanics* — scanning, page turns. A fixed screen rather than paper removes most of that confound.
⚠️ Pupil requires constant screen luminance, or you measure the pupillary light reflex instead of arousal.
Prosody appears nowhere in their tables. It is the contribution, and the bar to clear is 0.44.

**Tier 2 — worth having**

| Modality | Affect | Discrete | Note |
|---|---|---|---|
| Pixel intensity | 0.71 | 0.34 | Nearly free once eye frames exist. Requires fixed room lighting. |
| Gaze (yaw/pitch) | 0.69 | 0.25 | Already logged. See caveat below. |
| Blink | 0.70 | 0.11 | Arousal index; also marks line breaks during reading. |

**Gaze caveat in your favour:** they ran 15 generic statistical descriptors over yaw/pitch. Your task supports reading-specific features they never computed — fixation duration per word, regression rate, reading rate, and eye–voice span. Known script text plus own-voice audio makes those computable. 0.69 is not gaze's ceiling in your design.

**Tier 3 — validation only**

| Modality | Affect | Discrete | Verdict |
|---|---|---|---|
| Nosepad PPG | 0.70 | 0.12 (chance = 0.11) | Keep for RQ3 agreement with chest strap. Not a predictor. |
| Chest ECG | 0.69 | 0.13 (chance) | Reference channel for RQ3. |

Speech makes both worse — talking disrupts respiration, which propagates into cardiac variability. Your participants speak throughout.

**Skip**

| Modality | Why |
|---|---|
| Micro-expression (LBP-TOP) | 0.69 / 0.14. High complexity, near-zero payoff. |
| Fisherface | 0.70 / 0.22. PCA→LDA fitted per target — overfits at small N. |
| Egocentric RGB | **Absent from every results table.** Recorded at 1408×1408, produced no features. |
| EDA, respiration belt | Sensors not available to this project. |
| Personality prediction | 0.59 vs 0.53 random, ± 0.49. Not a real result. |

### 7.3 Engineering blocker this creates

Pupil, pixel intensity, blink and Fisherface all require **raw eye-camera frames** (640×480 @ 90 fps per eye). V5.1 registers `register_eye_gaze_callback`, which returns a derived yaw/pitch/depth vector — **not images**.

**Open question: does the Client SDK expose ET camera frames live, or only into the VRS recording?** If VRS-only, eye features become an offline extraction step. Workable, but it changes the pipeline, and it is far better to know before ten participants are recorded than after.

Everything in Tier 1 and Tier 2 except IMU and prosody depends on that answer.

### 7.4 Protocol furniture worth copying

Cheap, validated, and otherwise learned the hard way:

- 5-second fixation cross before each block — recalibrates gaze tracking
- Neutral washout between emotional blocks — prevents carryover
- Self-report after **every** block, not once per condition — this is how they got ~16 labelled events per participant instead of 3
- Per-participant feature standardisation to [0,1] — what makes leave-one-subject-out generalisation work when baselines differ across people
- Leave-one-subject-out evaluation — the honest protocol; use it

### 7.5 Gaps this project fills

| Their gap | Evidence | This project |
|---|---|---|
| No speech analysis | Audio appears in no feature list or table, despite participants speaking in Jenga and "Try to Laugh" | Prosody from own-voice contact mic |
| No no-device control | All 43 participants wore glasses in every recording | Condition C2 |
| Sparse low-arousal-negative data | Their stated limitation | Velten negative scripts target exactly this quadrant |
| Retrospective self-report labels | Their stated limitation | Per-block ratings; optionally continuous annotation |

### 7.6 Constraints this project inherits

- **No deep learning.** It lost at N = 43; this study will be smaller.
- **"Aria predicts V/A/D" is not available as a contribution.** Already demonstrated at 0.75.
- **Classical ML with engineered features and LOSO is the appropriate ceiling** — and now a citable choice rather than a concession.

---

## 8. One-sentence positioning

> egoEMOTION showed that egocentric glasses can read affect from someone *watching* — better than a full physiological rig — but only from participants who were not speaking, with no no-device control, and with the authors' own note that the low-arousal-negative quadrant is under-sampled. This project addresses all three.
