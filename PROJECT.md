# PROJECT.md — read this when lost

One page. Everything else is detail.

---

## What the project is

People read an emotional first-person script out loud while wearing Meta Aria Gen 2 glasses.
The glasses record their eyes, voice, heart rate, and head motion.
Question: **can the glasses tell how the person felt?**

That's it. No VR headset. No AI writing stories. The participant reads a script, the glasses watch.

---

## The three conditions

| | What happens |
|---|---|
| **1** | Reads script, wearing Aria |
| **2** | Reads script, no Aria |
| **3** | No script, wearing Aria |

- **1 vs 3** → does reading an emotional script change the signals? (this is where your ML data comes from)
- **1 vs 2** → do the glasses change how people behave? (this is the honesty check)

Everyone does all three.

---

## What you already have

A working system (V5.1) that:
- connects to the glasses and streams data ✅
- records eyes, heart rate (PPG), head motion, video, audio ✅
- saves everything to disk with a manifest ✅
- shuts down cleanly ✅

It's good. The hard plumbing is done.

---

## What's wrong with it

It's a **voice assistant** ("Hey Meta, what am I looking at?"). You need a **silent recorder**.

Five things to fix:

1. **It doesn't record long speech.** It only saves ~4-second clips when someone asks a question. A 10-minute reading produces zero audio files. ← biggest problem
2. **No way to mark which condition you're in.** Sessions are just named by participant. Nothing says "this was condition 2."
3. **The assistant talks back.** If it triggers mid-script, the glasses speak out loud into their own microphones. Must be turned off.
4. **Possible clock bug.** Sensor summaries may be silently empty. Takes 10 minutes to check. Check it first.
5. **Windows won't work.** The Aria SDK is Mac/Linux only. Collect on the Mac.

---

## What's blocking you (not code)

**IRB / ethics approval.** Nobody has started it. It takes weeks. The code takes days.
This is your real deadline, not the software.

---

## Two things to tell your mentor

**1. "Gaze dispersion" won't work.**
They want to measure how your eyes wander around a room. But someone reading a script stares at the text. Their eyes aren't wandering.

Instead measure how they read: how long they pause on words, how often they re-read, how fast they go, and how far their eyes run ahead of their voice. Better data, and only your setup can capture it.

**2. Condition 3 should be a boring script, not silence.**
Right now condition 3 is "say nothing." So when you compare it to condition 1, you can't tell if the difference came from the *emotion* or just from *talking*.

If condition 3 is reading a neutral script instead, then the only difference is the emotion. Clean comparison.

---

## Four things to do this week

Each is small. None depend on each other.

1. Run `python inspect_sensor_session.py` on an old session. Compare the manifest counts to `samples_in_window` in a query snapshot. If counts are big but `samples_in_window` is 0 → that's the clock bug.
2. Send one email: **who approves human studies here?**
3. Check whether microphone channel 7 is the nosepad contact mic or just the loudest regular mic.
4. Confirm you're collecting on the Mac.

**And ask your mentor: how many participants?** They never said. It decides whether this is a pilot or a real study.

---

## Where the other files are

```
Aria 2/
├── PROJECT.md                          ← you are here
├── PROBLEM-STATEMENT.md                ← the formal write-up
├── aria_gen2_watch_and_tell_latest_v5_1/   ← the code (V5.1)
└── docs/                               ← everything else
```

| File | What's in it | When to open it |
|---|---|---|
| `PROJECT.md` | this page | when lost |
| `PROBLEM-STATEMENT.md` | proposal-ready: the problem, the gap, RQ1–RQ4, scope, success criteria | writing the proposal or report |
| `docs/design-after-mentor-answers.md` | what the mentor's answers changed, the three decisions they left to you, the egoEMOTION argument | before the next mentor meeting |
| `docs/codebase-review-v5_1.md` | full code review, bugs, V6 build order | when you sit down to code |
| `docs/egoEmotion.pdf` | the paper closest to this project | when you need its numbers |
| `docs/research-space-map.md` | the original exploration — 7 possible interpretations | mostly historical; 6 of the 7 are ruled out |
| `docs/v5_1.md` | the original one-page summary of the system | superseded by the code review |

---

## If you only remember one thing

The code is further along than the study is.
Stop building for a bit. Get IRB moving and get a participant count.
Then build the silent recorder.
