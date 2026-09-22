---
title: "Product Brief: AI Language Teacher"
status: ready
created: 2026-09-22
updated: 2026-09-22
---

# Product Brief: AI Language Teacher

## Executive Summary

**AI Language Teacher** is a local desktop teacher (Electron + Vue + Python) built around a closed teaching cycle: goals and placement → living long-term plan → scheduled voice lessons → reminders and between-lesson practice → plan revision from errors and performance.

**v1** is personal-first: English target, Russian as the language of explanation. Denys already reads and works in English text but stalls on speaking and listening. Differentiation is teacher-like continuity and adaptation — not a proprietary model.

**Success** is about six months of level-scaled progress toward usable conversation and listening comprehension. **Later:** multi-language open source, flexible L1/target pairing, optional web client. Hard v1 boundaries are in Scope below.

## Scope

**In for v1**

- Desktop app (Electron + Vue UI + Python teacher backend)
- English target; Russian explanation/L1
- Configurable onboarding (goals, interests, emphasis, 30/45/60 min sessions, weekly cadence)
- Placement that includes speaking and listening
- Living long-term plan that revises with performance
- Adaptive lesson templates: study-heavy, oral practice, transfer / weak-spot repair
- Voice dialogues + listening; error review into the plan; vocab micro-sessions + reminders between lessons
- Certificate-oriented planning/practice when selected at intake
- Pronunciation as a first-class practice thread (best-effort with available STT/TTS)

**Out for v1**

- Other target languages (architecture may anticipate them)
- Fully offline LLM (remote or API models with locally stored keys are acceptable)
- Polished open-source (OSS) packaging for arbitrary learners
- Web client

Pedagogy quality depends on placement, error memory, and plan revision — not on a model moat.

## The Problem

Reading and working in English is already comfortable; **speaking and listening are not** (films, calls, podcasts, real conversation). Without a structured oral loop — plan, practice, feedback, cadence — progress stays in the text comfort zone. There is no human-teacher habit to lean on; building a local desktop teacher is how to get structured lessons and voice practice without SaaS dependency or scheduling a person.

## The Solution

On first open, the teacher runs intake (why learn, interests, desired outcomes), a **speaking + listening** placement, then proposes path options, skill emphasis, session length, and weekly frequency. It builds an approximate living long-term plan that can change with performance and learning speed, then starts lesson one.

Ongoing, it chooses a lesson layout from results and recurring errors:

- **Study-heavy** — review, new material/words, checks, error review
- **Oral practice** — dialogue, listening, error review
- **Transfer / weak-spot repair** — recycle error patterns through new listening and role-play, then capture items for review

Between lessons: short vocabulary micro-sessions (5–10 min), possibly several times, with reminders. (Minute-level lesson timings live in the addendum for PRD/curriculum work.)

## What Makes This Different

The product is the **closed teaching loop and accountability**, not another AI chat. Local desktop and voice are the delivery surface for continuity — plan → lesson → adapt → remind — for learners who need progress in speaking and listening, not more text drills.

## Who This Serves

**Primary (v1):** Denys — personal English learner with strong reading/work literacy and weak speaking/listening; Russian L1 for explanations.

**Secondary / later (OSS):** language learners with varied goals and weak spots. Generalization comes from configurable intake, placement, and emphasis — not from hard-coding one gap into every path.

## Success Criteria

Horizon is about **six months**, scaled by placement level.

1. Sustain work/everyday conversation (~15–20+ minutes) with less freezing; transfer increasingly to real people.
2. Follow the main thread of familiar-topic films, calls, and podcasts.
3. Maintain current reading strength (not the v1 breakthrough).
4. If certificate path chosen: measurable progress against that exam’s skill profile (passing the exam is not a required v1 outcome unless set later).
5. Pronunciation clear enough for those conversations, with deliberate improvement work — “native-identical” is an investment ambition, not a ship gate.

## Vision

An **open-source, multi-language** teacher that keeps the same closed loop. Learners choose **target** and **native/explanation** language from the supported set. Desktop stays home; a **web** surface may follow without abandoning the teaching model.
