# Mini-ADR — Mid-Course Project

## Feature selection

Chose **due dates + overdue filter** and **search + combined filters** from
the five core options (comments, tags, and activity log were not built —
the brief asks for exactly two). Reasoning: both extend the existing
`GET /tasks` query-param pattern that `status`/`priority` filtering already
established in Module 2/3, instead of introducing a new resource type
(comments would need a new sub-resource; activity log would need to hook
into every mutating route). They also pair naturally — the brief's own
description of the search feature mentions combining with "tag/due-date if
implemented," so building both together produces one coherent filter bar
instead of two disconnected additions. Both are fully visible and usable in
the Kanban UI, satisfying the "at least one visible in the frontend"
requirement with room to spare.

## Feature 1: Due dates + overdue

- `due_date: Optional[date]` added to `TaskCreate`, `TaskUpdate`, and
  `TaskResponse`. Pydantic's built-in `date` type parsing rejects malformed
  input with `422` automatically — no hand-written format validation.
- `is_overdue` is a Pydantic `@computed_field` on `TaskResponse`, **not a
  stored field**. Rule: `due_date < today() and status != Done`. Computed
  fresh on every response.
- The same rule is used for the `overdue` query filter, via a single shared
  function (`is_task_overdue` in `app/models.py`) — used by both the
  computed field and `storage.get_all_tasks`, so the definition can't drift
  between the two call sites.

**Alternatives considered and rejected:**
- *Store `is_overdue` as a persisted flag.* Rejected — would go stale the
  moment the calendar moves past a task's due date without any edit
  happening to that task.
- *Compute overdue in the frontend (JavaScript `Date` math).* Rejected —
  duplicates the business rule in two languages, and any other API consumer
  (not just this frontend) would have to reimplement it correctly, including
  the Done-task exception.
- *Use `datetime` with time-of-day precision.* Rejected as unnecessary
  complexity for a day-level due date in a learning project — adds
  timezone handling with no real benefit here.

## Feature 2: Search + combined filters

- `search: Optional[str] = None` added to `GET /tasks`, matched
  case-insensitively as a substring against `title` OR `description`.
- Combines with `status`, `priority`, `assignee`, and `overdue` via plain
  sequential AND-filtering in `storage.get_all_tasks` — each filter narrows
  whatever the previous one already returned.
- `assignee` was added as a small filter alongside the two chosen features,
  not as a third feature — it's the same one-line equality-filter pattern
  as `status`/`priority`, and the brief explicitly lists "assignee" as one
  of the example filters to combine with search.

**Alternatives considered and rejected:**
- *Client-side filtering of an already-fetched task list.* Rejected — see
  the corrected assumption in `docs/midcourse/user-stories.md`; it isn't
  testable against the real API contract and can drift from what the
  backend actually supports.
- *Full-text search with relevance ranking or word-boundary matching.*
  Rejected as over-engineering for a flat in-memory task list in a learning
  project — a plain substring match is sufficient and easy to reason about.
- *A separate `/tasks/search` endpoint.* Rejected — search is just another
  filter on the same resource, not a different one; extending `GET /tasks`
  keeps one source of truth for "what tasks match these criteria."

## Explicitly out of scope for this project

Tags, task comments, and an activity log (the other three core options),
plus every "optional extension" (bulk operations, saved views, frontend-only
polish) — per the brief's own guidance that those are bigger than needed
and don't primarily assess backend/testing skill. No new persistence layer
was introduced; both features extend the existing in-memory `TaskResponse`
model from Module 2, so there were no storage/migration decisions to make.
