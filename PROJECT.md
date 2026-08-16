# PROJECT.md — read this when lost

One page. Everything else is detail. **If any other file disagrees with this one, check `HISTORY.md` first** — the project pivoted once already (2026-08-17) and some docs still describe the old design on purpose, as a record.

---

## What the project is

People read short first-person story scenes on a screen, wearing Meta Aria Gen 2 glasses. Each scene ends in a decision: 4 options, each representing a different moral framing (care, fairness, loyalty, authority, sanctity — Moral Foundations Theory). They pick one, rate how sure they were, move to the next scene. Several scenes per story, several stories per person.

The glasses record their eyes, heart rate, and head motion the whole time — especially in the seconds before each click.

Question: **can we build a picture of someone's moral profile from how they behaved and reacted while deciding — not just from which button they pressed?**

No VR headset. No spoken answers — selection is by click. No AI writing the stories — those come from outside this project.

---

## Why sensors at all

If the answer were "just tally which option each person picked," you wouldn't need Aria — that's a 4-button survey. The actual bet: two people can pick the same option, one instantly and one after visible struggle, and that struggle — pupil, heart rate, head motion, how long they hesitated — is invisible to the button press. The glasses are there to catch that.

---

## What you already have

A working system (V5.1) that:
- connects to the glasses and streams data ✅
- records eyes, heart rate (PPG), head motion, video ✅
- saves everything to disk with a manifest ✅
- shuts down cleanly ✅

The hard plumbing is done. It's currently shaped like a voice assistant ("Hey Meta, what am I looking at?"); it needs to become a silent recorder instead. See `ROADMAP.md` Goal 1 for exactly what changes.

---

## What's blocking you (not code)

**IRB / ethics approval.** Nobody has started it. It takes weeks. The code takes days.
This is still your real deadline, same as before the pivot.

---

## Still open

- **How many participants.** Never answered.
- **Which tool shows the stories.** Requirement is just "QR codes + clean 4-option layout" — not picked yet.
- **The stories themselves.** Coming from outside this project — nothing downstream can start until at least one arrives, correctly tagged.

Full list with owners: `PROBLEM-STATEMENT.md` §8.

---

## Where the other files are

```
Aria 2/
├── PROJECT.md                          ← you are here
├── PROBLEM-STATEMENT.md                ← the formal write-up (current design)
├── HISTORY.md                          ← what changed, when, and why
├── ROADMAP.md                          ← the 3 goals: build, collect, infer
├── design/
│   ├── HLD.md                          ← system architecture
│   └── LLD.md                          ← schemas, formats, what's still TBD
├── aria_gen2_watch_and_tell_latest_v5_1/   ← the code (V5.1)
└── docs/                               ← reference material
```

| File | What's in it | When to open it |
|---|---|---|
| `PROJECT.md` | this page | when lost |
| `PROBLEM-STATEMENT.md` | the problem, the gap, RQ1–RQ4, scope, success criteria — **current design** | writing the proposal or report |
| `HISTORY.md` | the pivot, and everything superseded by it | before trusting an older doc |
| `ROADMAP.md` | 3 goals — build the codebase, run the study, do the ML — as checklists | picking what to do next |
| `design/HLD.md` | how the pieces fit together: Aria, the story tool, QR sync, feature extraction, modeling | before building or explaining the system |
| `design/LLD.md` | exact data formats, the QR schema, the foundation-tagging schema, what's engineering-done vs. research-open | when you sit down to code or brief the content team |
| `docs/codebase-review-v5_1.md` | full V5.1 code review, bugs, code-quality notes | still current for engineering, superseded for study design |
| `docs/egoEMOTION-paper-summary.md` | closest prior paper, full result tables, which modalities work | deciding what to engineer/analyze next |
| `docs/IKS-vs-MFT.md` | does Moral Foundations Theory fit Indian ethics — where it does, where it doesn't | designing story content, picking the validation questionnaire |
| `docs/egoEmotion.pdf` | the paper itself | verifying a number before you quote it |
| `docs/design-after-mentor-answers.md`, `docs/research-space-map.md`, `docs/v5_1.md` | earlier design work, **now superseded** | historical only — see `HISTORY.md` |

---

## If you only remember one thing

Get IRB moving and get a participant count — both still true from before the pivot.
Then: `ROADMAP.md` Goal 1, build the silent recorder.
