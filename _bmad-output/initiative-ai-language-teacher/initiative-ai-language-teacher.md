---
type: initiative
title: "AI Language Teacher (v1)"
parent: none
covers: [CAP-1, CAP-2, CAP-3, CAP-4, CAP-5, CAP-6, CAP-7, CAP-8, CAP-9, CAP-10, CAP-11, CAP-12, CAP-13, CAP-14, CAP-15]
after: []
assignee: ""
risk: high
---

# AI Language Teacher (v1)

## Description

Personal desktop AI English teacher (v1): Electron + Vue UI client, Python teacher service (FastAPI, LangGraph, SQLite), hexagonal core. The product contract lives in the initiative SPEC; this initiative delivers that contract for the personal desktop cut.

## Outcome

Denys can sustain spoken English practice tied to a revisable Living plan and Telegram cadence (SM-1–SM-4), without hiring a tutor — voice + plan + reminders are non-negotiable.

## Done when

1. SM-1: Hold sustained work/everyday conversation (~15–20+ minutes) with less freezing; transfer increasingly to real people.
2. SM-2: Follow the main thread of familiar-topic films, calls, and podcasts.
3. SM-3: Maintain current reading strength (not the v1 breakthrough).
4. SM-4: Pronunciation clear enough for those conversations, with deliberate improvement.
5. CAP-1 through CAP-15 are live for the single local Learner on desktop + Telegram cadence.
6. NFR-1 (no PII to LLM), NFR-3 (no silent hang), and NFR-4 (documented Settings) hold.

## Boundaries

Personal desktop v1 (English target, Russian explanations), local teacher service, Telegram Micro-lessons/reminders. Not multi-user web, not additional target languages, not fully offline LLM — see SPEC / PRD non-goals.

- Touch point: OS app-data Config/SQLite — secrets and learner store; owner: epic-desktop-teacher-foundation
- Touch point: Telegram Bot API — delivery only; owner: epic-telegram-cadence-progress-replan

## References

- spec — _bmad-output/initiative-ai-language-teacher/spec-ai-language-teacher/spec-ai-language-teacher.md, section Capabilities
- prd — _bmad-output/initiative-ai-language-teacher/prd-ai-language-teacher/prd-ai-language-teacher.md
- architecture — _bmad-output/initiative-ai-language-teacher/architecture-ai-language-teacher/architecture-ai-language-teacher.md
- ux — _bmad-output/initiative-ai-language-teacher/ux-ai-language-teacher/ux-ai-language-teacher.md
- constraint — same SPEC/PRD, NFR-1 privacy and non-goals

## Notes

- Decision: migrated from v6 epics/sprint-status on 2026-10-03 (method migration-1).
- Decision: three unmatched done build records become epic-2 entries 8–10 (Outlook week-grid, listening player, cloud Voice).
