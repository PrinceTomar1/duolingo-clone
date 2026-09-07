# Walkthrough

Why each file exists and what decision it encodes. Written to revise from.

The single idea the whole codebase is organised around: **the client renders,
the server decides.** If you remember one thing walking into the interview,
remember that every design choice below falls out of it.

---

## Part 1 — The six questions

### Why layer FastAPI into routers → services → models?

Because each layer answers a different question, and mixing them makes all three
untestable.

- `routers/` answers *"what did the HTTP request mean?"* — parse the path, call
  one service, shape the result into a Pydantic model. A handler has no `if`.
- `services/` answers *"what should happen?"* — every rule lives here. They take
  a `Session` and plain values; they know nothing about HTTP.
- `models/` answers *"what is true?"* — shape, constraints, cascades.

Three payoffs I can point at in the code:

1. **The tests.** `test_xp.py` plays whole lessons — start, answer, complete —
   by calling `lesson_service` directly. No HTTP client, no app fixture. That is
   only possible because no rule needs a request object.
2. **One place for status codes.** Services raise `SkillLockedError`; the handler
   in `main.py` maps it to 403. No handler repeats a try/except, and changing the
   code for "locked" is a one-line edit.
3. **Reuse.** `seed_data.py` calls `gamification_service.refresh_streak` and
   `achievement_service.sync_achievements` — the same functions the API uses. The
   demo learner's 3 unlocked badges are unlocked by the real unlock logic reading
   the real seeded state, not hardcoded.

The counter-question to expect: *"isn't this over-engineered for a 12-table
app?"* The honest answer is that the layering paid for itself twice during the
build — the seed script reusing the services, and the tests needing no HTTP.

### Why grade on the server?

Because the browser is not trustworthy, and because grading is the product.

If `GET /lessons/{id}` returned `correct_answer`, anyone with devtools could read
the whole answer key, or skip straight to `complete` and award themselves XP.
So the answer key is never serialised — and crucially, **not by remembering to
delete it**: `ExerciseRead` in `schemas/lesson.py` has no `correct_answer` field
at all. A future developer cannot leak it by forgetting a `del`.

`test_api.py::test_never_returns_the_answer_key` asserts the raw response text
contains none of `correct_answer`, `explanation` or `accepted`. That test is the
one I would keep if I could keep only one.

The interesting case is **match-pairs**, which genuinely needs feedback per link
— a board that only reveals which of five links was wrong at the end is
unplayable. Shipping the mapping would have leaked it. So the client asks about
one link at a time (`POST /attempts/{id}/match-pair`) and gets back a single
boolean — exactly the bit the game shows anyway. It costs no heart, because a
board can only be finished by matching everything, which is how the real game
treats this exercise too.

### Why `daily_xp` instead of a streak counter?

A counter is a number nobody can check. If a bug double-increments it, the
damage is silent and permanent; there is nothing to recompute from.

`daily_xp` is a ledger — one row per learner per day with any XP, with
`UNIQUE(user_id, date)` making a duplicate structurally impossible. The streak
is then a *property of which rows exist*:

```python
def compute_streak(active_days: set[date], today: date) -> int:
    if today in active_days:            cursor = today
    elif today - 1 day in active_days:  cursor = today - 1 day
    else:                               return 0
    length = 0
    while cursor in active_days:
        length += 1
        cursor -= 1 day
    return length
```

Pure, and it makes all three required behaviours fall out of one loop:

- **Increments once per day:** a second lesson lands on the same row, so the set
  of days does not change.
- **Unchanged same-day:** same reason. There is no increment to suppress.
- **Resets on a gap:** the `while` stops at the first missing day.

Accepting *yesterday* as a starting point is deliberate: a learner who has not
practised yet today has not lost their streak — they lose it when the day rolls
over with no row.

`user_stats.current_streak` still exists, as a **cache** for cheap reads.
`refresh_streak` is the only function allowed to write it, and it always
recomputes from the ledger. The cache can be wrong for a moment; it can never be
the source of truth.

The payoff is demonstrable: Settings → *Advance one day*. Nothing is incremented
or decremented — `compute_streak` simply sees a different `today`. The 7-day
streak survives one quiet day and collapses on the second.

### Why lazy heart regeneration?

The obvious implementation — a scheduled job that gives every learner a heart
every 30 minutes — is wrong at every scale. At one user it needs infrastructure
that does not exist; at a million it is a million writes per half hour, almost
all of them to learners who are asleep and whose hearts are already full.

Instead one column, `hearts_updated_at`, anchors the calculation and hearts are
derived on read:

```python
earned = (now - hearts_updated_at) // 30 minutes
hearts = min(5, hearts + earned)
```

Three details worth knowing, because they are the ones an interviewer probes:

1. **The leftover is banked.** After 75 minutes the anchor advances by 60, not
   to `now` — so the remaining 15 minutes still count toward the next heart. A
   naive `hearts_updated_at = now` would silently rob the learner.
   (`test_hearts.py::test_partial_interval_is_not_discarded`)
2. **A full bar does not bank credit.** Once at 5 the anchor snaps to `now`, so
   a learner who has been away for a week does not lose the next heart instantly.
3. **The first loss from a full bar starts the timer.** Otherwise the anchor
   would be stale by days and the next heart would arrive immediately.

The trade-off: hearts only "arrive" when someone looks. Which is fine — nothing
observes them except the learner.

### Why JSON payload columns for exercises?

The five types have genuinely different shapes. A word bank has tiles and an
ordered answer; match-pairs has two columns and a mapping; a typed answer has
neither. The three options were:

| Option | Cost |
|---|---|
| Five tables + a join per type | Every lesson fetch becomes five outer joins for nine rows. |
| One wide table | Mostly-NULL columns; every new type is a migration. |
| **One table, JSON payload** | No database-level shape validation. |

I chose JSON. A lesson is one indexed query (`WHERE lesson_id = ?`), and adding
a sixth exercise type is a content change plus one pure grader function plus one
entry in the dispatch table — **no migration, and no router change.**

What I gave up is the database validating the payload shape. That is mitigated
by the fact that exactly one module ever reads it (`answer_grader`), the graders
are defensive about malformed input, and the tests run against real
factory-generated content rather than invented fixtures. If this grew, the next
step is a Pydantic model per type validated on write — not five tables.

The frontend gets the same guarantee a different way: `Exercise` in
`types/api.ts` is a **discriminated union** on `type`, so `ExerciseView`'s switch
narrows the payload automatically and a new type is a *compile error* until it is
handled.

### How would this scale to 1M users?

In the order things would actually break:

1. **SQLite → Postgres.** A `DATABASE_URL` change. The models and migrations are
   dialect-agnostic apart from the SQLite `foreign_keys` pragma, which is already
   conditional on the URL scheme.

2. **The leaderboard breaks first.** `GET /leaderboard` groups over `daily_xp`
   for every user on every request — a growing scan. Fix: leagues of ~30 people
   (which is what Duolingo actually does), materialised into a `league_standing`
   table by a job every few minutes, read by primary key. Ranking a million
   people against each other is not a product requirement anyone has.

3. **`user_stats` is the one hot row per learner.** Every completion writes it.
   It is already a single-row primary-key update with no cross-user contention,
   so it shards perfectly by `user_id`. The XP write is additive and the streak
   write is idempotent (recomputed, not incremented), so both are safe to retry
   or move behind a queue.

4. **Course content is read-mostly and identical for everyone** — the natural
   cache. `GET /lessons/{id}` never varies by user, so it goes behind a CDN or
   Redis with a content-version key. `GET /course/path` is per-user but already
   **three queries regardless of course size** (units+skills, lesson counts,
   crowns) — deliberately, no N+1.

5. **`daily_xp` grows at one row per active user per day** — ~365M rows/year at a
   million DAU. Partition by month; the streak walk only ever touches recent
   days, and old partitions can be rolled into a summary table.

6. **What does *not* change:** the grader is pure and stateless, so it scales
   horizontally for free. That is the point of having kept it pure.

---

## Part 2 — The files

### Backend

| File | Why it exists / what it decides |
|---|---|
| `core/config.py` | One `Settings` object; nothing else reads `os.environ`. The gamification constants (max hearts, regen minutes, XP amounts) live here rather than as literals, because they are product decisions that get tuned — and the tests assert against the same constants, so a change can't silently break the formula. |
| `core/database.py` | Engine, `SessionLocal`, `get_db`. Contains the one line most SQLite projects miss: `PRAGMA foreign_keys=ON` per connection. Without it every cascade rule in the schema is decoration. |
| `core/clock.py` | The single source of "now". Nothing else calls `datetime.now()`. This is what makes the streak rules testable without sleeping, and what `/dev/advance-day` moves. Process-local and not persisted — it's a demo aid, so a restart must return to real time. |
| `models/enums.py` | `ExerciseType` and `SkillState`, in their own module so Pydantic schemas can import them without pulling in SQLAlchemy. |
| `models/user.py` | Deliberately thin — identity only. Mutable game state lives in `user_stats` so a hearts write never contends with a profile read. |
| `models/course.py` | `Course → Unit → Skill`. `UNIQUE(parent_id, order_index)` on each: two siblings can never occupy the same slot on the path. |
| `models/lesson.py` | `Lesson` and `Exercise`. The `payload` / `correct_answer` JSON decision, documented in the class docstring. |
| `models/progress.py` | `UserProgress` (one row per user+skill, `UNIQUE`) and `LessonAttempt`. The attempt row is what makes the flow tamper-proof: the client holds only an `attempt_id`. |
| `models/stats.py` | `UserStats` (PK **is** the FK — exactly one row per learner, enforced by the schema) and the `DailyXp` ledger. |
| `models/achievement.py` | `Achievement.metric` names the stat the badge tracks, which turns unlocking into a generic loop instead of an `if/elif` over badge codes. `unlocked_at IS NULL` distinguishes "in progress" from "done" without a redundant boolean. |
| `services/answer_grader.py` | **Pure.** One function per type, plus a dispatch table. `normalize()` folds case, accents and punctuation — accents especially, because most learners cannot type them and refusing the answer teaches nothing. `format_correct_answer` renders the red bar's line, and is only ever called *after* grading, for the exercise just answered. |
| `services/gamification_service.py` | Hearts, the XP formula, the ledger, streaks. The rule-encoding functions (`regenerated_hearts`, `calculate_lesson_xp`, `compute_streak`) are pure and take their inputs explicitly, so the tests assert the rules with no database and no clock. |
| `services/path_service.py` | Derives skill state; **never stores it**. `build_path` is 3 queries regardless of course size. `sync_unlock_flags` persists `is_unlocked` as a denormalised convenience for the lesson-start guard, but `build_path` remains the authority and rewrites it. |
| `services/achievement_service.py` | Computes every metric in one pass, then walks the definitions generically. Idempotent: `unlocked_at` is only written when currently NULL, so a replayed request cannot re-toast a badge. |
| `services/lesson_service.py` | The only module that mutates progress. `complete_attempt` is ordered deliberately — XP is banked *before* the streak is recomputed, unlock flags refreshed *before* achievements sync — so every value in the returned summary reflects the same post-lesson world. `_award_crown` grants a crown only on the *first* completion of a specific lesson, so a learner cannot farm a skill by replaying its easiest lesson. |
| `services/exceptions.py` | Domain errors carrying their own `status_code`. Services raise meaning; `main.py` decides transport. |
| `schemas/lesson.py` | `ExerciseRead` — the security boundary. It has no `correct_answer` field, so the leak is structurally impossible. |
| `routers/*.py` | HTTP only. If a handler grows an `if`, that logic belongs in a service. |
| `routers/dev.py` | Mounted **only** when `DEBUG` — in production the routes do not exist, rather than returning 403. |
| `main.py` | App, CORS, router registration, and the single `DomainError` handler. |
| `seed/content.py` | Pure data: vocabulary and sentence pairs. |
| `seed/exercise_factory.py` | Deterministic generation — seeded `Random` per (skill, lesson), so re-seeding produces byte-identical exercises and the idempotent upsert has nothing to change. |
| `seed/seed_data.py` | Idempotent by convergence: content upserted on natural keys, demo learners' derived rows rebuilt. |

### Frontend

| File | Why it exists / what it decides |
|---|---|
| `tailwind.config.ts` | Duolingo's palette as named tokens. No raw hex anywhere else except colours the API supplies. A rebrand is one file. |
| `lib/api.ts` | The **only** module that calls `fetch`. Base URL from `NEXT_PUBLIC_API_URL` — no hardcoded localhost, which is what makes the Vercel build work against a deployed backend with no code change. |
| `types/api.ts` | Hand-written mirrors of the Pydantic models. `Exercise` is a discriminated union — the compiler, not a code review, catches an unhandled type. |
| `lib/theme.ts` | Theme constants with **no** `"use client"`. A value imported into a server component from a client module becomes a client-reference proxy, not the value — which silently turned the storage key into `{}` in the pre-paint script. This bug was real, and this module is the fix. |
| `lib/clsx.ts` | Three lines instead of a dependency. |
| `lib/icon-paths.ts` | Every icon as SVG path data, hand-drawn. Smaller than an icon package and changeable one glyph at a time. |
| `lib/answers.ts` | Turns the in-progress draft into the API's answer envelope. CHECK is enabled precisely when this returns non-null, so "is the answer complete?" and "what do we send?" are one rule in one place. |
| `lib/sound.ts` | Two tones synthesised with the Web Audio API rather than shipped as MP3s. Every call is wrapped defensively — a blocked sound must never break a lesson. |
| `components/ui/Button.tsx` | The 3D button. `border-b-4` in the shadow colour reads as the side wall; pressing removes it and translates down by the same 4px, so it depresses without shifting layout. A `disabled` button always renders in the locked style, so a caller cannot make a greyed-out button that still looks pressable. |
| `components/path/SkillPath.tsx` | The winding trail. The sine runs over the node's position along the **whole path**, not within its unit — otherwise the pattern restarts at every header and reads as three separate columns. Amplitude is `min(26vw, 120px)`: fixed on desktop, viewport-relative at 375px so a node can never be pushed off-screen. |
| `components/lesson/LessonPlayer.tsx` | Owns the flow — draft, check, feedback, advance — and delegates every rule to the server. It never decides whether an answer is right. |
| `components/exercises/ExerciseView.tsx` | The exhaustive switch over the union. Adding a type here is a compile error until handled. |
| `components/exercises/MatchPairs.tsx` | Only *routes* taps; the server decides each link. |
| `store/useLessonStore.ts` | One run's state. Note what is **not** in it: whether an answer is correct. |
| `store/useSessionStore.ts` | The learner and their live stats, so the right rail, the lesson player and the shop all read one source. |
| `components/layout/AppShell.tsx` | The persistent chrome — and it deliberately does **not** wrap `/lesson/*`. Duolingo takes over the whole screen during a lesson; rendering the chrome behind a full-screen overlay would leave it reachable by keyboard. |

---

## Part 3 — Questions I'd expect, and the honest answers

**"Where's the authentication?"**
Not built. The assignment is about the learning experience, so the session is
the demo learner resolved by username at boot, and every endpoint takes an
explicit `user_id`. Adding real auth is a dependency that resolves the caller
and replaces that parameter — **the service layer does not change**, because no
service reads a request. That is the layering paying off.

**"Anyone can pass any `user_id`."**
Correct, and that is exactly the hole auth closes. Note what it is *not*: you
still cannot forge a grade, mint XP, or unlock a skill, because none of those
are client-side. The missing piece is identity, not integrity.

**"Why is `is_unlocked` stored if state is derived?"**
Because `start_attempt` needs to answer "may this learner open this lesson?"
without rebuilding the whole path. It is a cache, `build_path` is the authority,
and `sync_unlock_flags` rewrites it on every start and every completion.

**"Why does replaying a lesson still give XP?"**
Because practice should be rewarded — that is the point of a daily goal. But it
gives no second crown, because crowns count *distinct* lessons completed.
Otherwise you could gild a skill by replaying its easiest lesson.

**"What would you do next, with more time?"**
Three things, in order: (1) auth, which removes the `user_id` parameter
everywhere; (2) re-queueing wrong exercises later in the lesson, which is real
Duolingo behaviour I skipped; (3) frontend component tests — the backend has 118
tests and the frontend has typecheck and lint. That gap is the honest weak spot,
and it is the first thing I would close.
