# High-Level Design

Companion to `PROBLEM-STATEMENT.md`. Describes the shape of the system — components and how data flows between them — without implementation detail. See `LLD.md` for schemas and algorithms.

---

## 1. System overview

```
                         PARTICIPANT
                    (wearing Aria Gen 2)
                              │
              ┌───────────────┴───────────────┐
              │                                │
      looks at / reads                  clicks an option
              │                                │
              ▼                                ▼
    ┌───────────────────┐           ┌───────────────────────┐
    │   ARIA GEN 2       │           │  PRESENTATION TOOL      │
    │   (capture layer)  │           │  (Forms-shaped, TBD)    │
    │                     │           │                         │
    │  RGB (sees QR) ─────┼──┐        │  scene text + image     │
    │  Eye cameras        │  │        │  4-option decision       │
    │  Head IMU           │  │        │  QR code per page        │
    │  Nosepad PPG        │  │        │                         │
    │  VRS + JSONL log    │  │        │  → response log:         │
    └───────────────────┘  │        │    participant, story,   │
              │             │        │    scene, question,      │
              │             │        │    option chosen,        │
              │             │        │    confidence rating      │
              │             │        └───────────┬─────────────┘
              │             │                     │
              │             │  QR decoded from    │
              │             │  RGB frames give     │
              │             │  WHEN each page       │
              │             │  was shown            │
              │             ▼                     │
              │    ┌─────────────────────┐        │
              └───▶│   SYNC LAYER         │◀───────┘
                   │  (QR ID + timestamp   │
                   │   ↔ story/scene/       │
                   │   question ID)         │
                   └──────────┬────────────┘
                              │
                              ▼
                 ┌─────────────────────────┐
                 │  OFFLINE FEATURE          │
                 │  EXTRACTION               │
                 │  (projectaria_tools +     │
                 │   custom code)            │
                 │                            │
                 │  per decision window:      │
                 │  gaze allocation, pupil,   │
                 │  head-IMU dynamics,        │
                 │  PPG, choice latency       │
                 └──────────┬────────────────┘
                             │
                             ▼
                 ┌─────────────────────────┐
                 │  LABELING                 │
                 │                            │
                 │  choice → foundation tag   │
                 │  (from story content)      │
                 │  + MFQ-2 (intake, once)    │
                 └──────────┬────────────────┘
                             │
                             ▼
                 ┌─────────────────────────┐
                 │  MODELING & VALIDATION    │
                 │                            │
                 │  behavioral profile        │
                 │  (foundation tally)        │
                 │  refined by conflict       │
                 │  signal → compare to       │
                 │  MFQ-2 score               │
                 └────────────────────────────┘
```

---

## 2. Components

### 2.1 Capture layer — Aria Gen 2 + V5.1/V6 recorder

Records continuously and silently once a session starts: RGB (10 fps, sees whatever the participant is looking at, including the QR codes), eye cameras, head IMU, nosepad PPG. Raw stream goes to VRS (authoritative, lossless); a decoded JSONL log is written in parallel for fast inspection. No microphone use, no wake-word listening, no text-to-speech — the assistant behavior in V5.1 is fully disabled for data collection (`ROADMAP.md` Goal 1).

Reuses almost all of V5.1's existing plumbing: device connection, streaming, sensor callback registration, VRS recording, clean shutdown. Does **not** reuse: wake-word detection, the OpenAI Q&A loop, the audio ring buffer's question-capture logic — none of that applies to a silent recorder.

### 2.2 Content/response layer — presentation tool

Not Aria's job. A separate tool (page-per-scene, Forms-shaped) shows the story text/image and the four-option decision, and logs which option was clicked plus the confidence rating. This is where "what did they choose" lives. Final tool choice is open (§8 of the problem statement); the only fixed requirement is that each page carries a unique QR code and the option layout is clean enough for reliable clicking.

### 2.3 Sync layer — QR decode

Aria's RGB stream is scanned for QR codes at a modest sample rate (not every frame). Each detection yields `(qr_id, timestamp_ns)` on Aria's own clock. Because the presentation tool's own timestamps aren't reliable at page-turn granularity, **this is the only source of "when was scene/question X shown."** The presentation tool's response log supplies "what was chosen"; this layer supplies "when." Neither one can do the other's job.

### 2.4 Offline feature extraction

Runs after a session, not during it. Two tools involved:
- `projectaria-client-sdk` — live capture only, macOS/Linux only, already in `requirements.txt`.
- `projectaria_tools` — offline analysis of recorded VRS, works on any platform, needed here for machine-perception outputs (eye tracking, hand tracking) that aren't pulled live during capture.

For each decision window (§6 of the problem statement — QR-onset to click), compute: gaze allocation across the four options, pupil response, head-motion dynamics, cardiac signal from PPG, and raw latency. See `LLD.md` for exact feature definitions and what's still open.

### 2.5 Labeling

Two independent sources, deliberately kept separate so one can validate the other:
- **Behavioral** — which foundation was chosen, from the story content's foundation tags plus the presentation tool's response log.
- **Reference** — MFQ-2, administered once at intake, outside the glasses entirely.

### 2.6 Modeling & validation

Combines the behavioral tally with the physiological conflict signal from §2.4 into a profile, then checks that profile against the independent MFQ-2 score. This is the layer where RQ1 gets answered. Classical ML only (SVM/Random Forest-class methods), leave-one-subject-out evaluation — not deep learning, per the constraint established from egoEMOTION's own results at comparable N.

---

## 3. Data flow through one decision, narrated

1. Participant finishes reading a scene, the question page appears. Its QR code enters Aria's RGB frame within moments — sync layer logs `(question_id, t_onset)`.
2. Participant looks between the four options, deliberates, possibly scrolls back to re-read the scene. Aria's eye, IMU, and PPG streams record throughout — no special handling needed, they're always running.
3. Participant clicks an option and rates confidence. Presentation tool logs `(participant_id, question_id, option_id, confidence, t_submit_estimate)`.
4. Offline, the decision window is defined as `[t_onset, click_time]`. Click time itself is taken from the *next* QR detection (the following page's onset) as a cross-check where available, since the presentation tool's own timestamp isn't reliable at this grain.
5. Feature extraction runs over that window. `option_id` resolves to a foundation tag from the story content.
6. This repeats for every decision, across every story, for every participant.

---

## 4. Deployment split

| Machine | Runs | Why |
|---|---|---|
| Mac (or Linux) | Capture layer, `projectaria-client-sdk` | Client SDK has no Windows build |
| Any machine (this Windows box included) | Offline feature extraction, `projectaria_tools`, modeling | No live-device dependency |

---

## 5. Explicit non-goals

- No VR headset anywhere in the system.
- No live/on-device inference — every analysis step is offline, after a session ends.
- No voice capture or processing in the current design — the microphone streams are recorded (they come along with everything else) but nothing in this pipeline analyzes them.
- No deep learning in the modeling layer.
