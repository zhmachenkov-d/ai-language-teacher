# Addendum — AI Language Teacher

Detail for PRD/architecture; not part of the executive brief.

## Technical constraints (user-stated)

- **Backend:** Python; orchestration possibly LangGraph
- **Frontend:** Vue.js in **Electron**
- **Voice:** oral dialogues + listening comprehension
- **Deployment:** desktop-first / local app shell
- **LLM:** v1 may use remote/API models with local keys — not required fully offline
- **Audience trajectory:** personal use first → possible open-source later

## Open technical topics

- Local STT/TTS stack and how deep pronunciation scoring can go
- Data model for learner profile, SRS, lesson plans (local store)
- How certificate profiles are represented when a path is selected

## Lesson templates (timing detail)

Teacher selects layout from performance and error patterns.

**Study-heavy (~45 min bands):** warm-up/review 5–10 → new material 10–15 → new words 10–15 → checks 10–15 → error review 10–15.

**Oral practice:** warm-up/review 5–10 → spoken dialogue 10–15 → listening 10–15 → error review 10–15.

**Transfer / weak-spot repair:** warm-up on recurring errors 5–10 → short i+1 listening 8–12 → spoken role-play in a _new_ scenario 12–15 → shadowing / re-say corrected lines 5–8 → capture to review 2–5.

**Between lessons:** vocab (and related) micro-sessions 5–10 min, possibly multiple times per interval.

## Parked pedagogy (from landscape, not v1 commitments)

Personal-corpus SRS beyond vocab micros, richer i+1 graded input engine, blocked→interleaved scheduling science, pragmatics/discourse drills — candidates for later if the teacher loop lands.
