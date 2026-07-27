# User Stories — Mid-Course Project

Two features, chosen from the core options and scoped deliberately small:
**due dates + overdue filter**, and **search + combined filters**. Both
extend the existing `GET /tasks` query-param pattern (like `status`/
`priority` already did) rather than introducing a new resource type.

---

## Feature 1: Due dates + overdue filter

**Story 1** — As a team member, I want to set an optional due date on a task
so I can track when it needs to be finished.
- Acceptance criteria:
  - `due_date` is accepted on create and update as an ISO 8601 date
    (`YYYY-MM-DD`).
  - Omitting it leaves the task with no due date (`null`).
  - An invalid format (e.g. `"not-a-date"`) returns `422`.

**Story 2** — As a team member, I want overdue tasks to be visually flagged
so I notice them without checking dates by hand.
- Acceptance criteria:
  - A task is overdue when `due_date` is in the past **and** `status` is
    not `Done`.
  - Overdue tasks show an "Overdue" pill on their card.
  - A `Done` task with a past due date is never flagged overdue.

**Story 3** — As a team member, I want to filter the board to only overdue
tasks so I can triage what's late.
- Acceptance criteria:
  - `GET /tasks?overdue=true` returns only overdue tasks.
  - The "Overdue only" checkbox in the UI applies the same filter and can
    be combined with the other filters in the bar.

**Story 4** — As a team member, I want to change or clear a task's due date
so I can adjust plans without recreating the task.
- Acceptance criteria:
  - `PATCH /tasks/{id}` with a new `due_date` updates it.
  - `PATCH /tasks/{id}` with `due_date: null` clears it.
  - The card and the modal both reflect the change immediately.

**Story 5** — As a team member, I want "overdue" to always reflect today's
date, not a stale snapshot, so the board stays accurate without me editing
every task.
- Acceptance criteria:
  - `is_overdue` is computed fresh on every response, not stored.
  - A task that becomes overdue purely from time passing (no edits made) is
    correctly flagged the next time it's fetched.

**AI assumption corrected:** the first instinct was to store `is_overdue`
as a persisted boolean, set once at creation/update time — the same pattern
as `created_at`/`updated_at`. That was wrong: a stored flag would go stale,
since a task can become overdue purely by the calendar moving forward, with
no PATCH ever happening to refresh it. Corrected to compute it fresh on
every read instead (see `docs/midcourse/mini-adr.md`).

---

## Feature 2: Search + combined filters

**Story 1** — As a team member, I want to search tasks by title or
description so I can find a specific task without scrolling the whole
board.
- Acceptance criteria:
  - `GET /tasks?search=<text>` matches case-insensitively against `title`
    and `description`.
  - A search with no matches returns `200` and `[]`, never `404`.

**Story 2** — As a team member, I want to combine search with status and
priority filters so I can narrow results precisely.
- Acceptance criteria:
  - `status`, `priority`, `search`, and `overdue` filters combine with AND
    semantics.
  - `?search=report&status=ToDo&priority=High` returns only tasks matching
    all three at once.

**Story 3** — As a team member, I want a compact filter bar above the board
so I don't lose the Kanban layout while filtering.
- Acceptance criteria:
  - The filter bar (search box, status/priority dropdowns, overdue
    checkbox, clear button) sits above the three columns.
  - Columns and their empty-state placeholders stay visible even when a
    filter returns zero matches in one or more columns.

**Story 4** — As a team member, I want the board to update automatically as
I change filters, without a separate "apply" step.
- Acceptance criteria:
  - Changing the status/priority dropdown or the overdue checkbox refetches
    immediately.
  - Typing in the search box refetches after a short pause (debounced), not
    on every keystroke.

**Story 5** — As a team member, I want an invalid filter value to be
rejected clearly, so I know a typo is mine and not a broken board.
- Acceptance criteria:
  - `GET /tasks?status=<not a real status>` returns `422`, not a silently
    empty or broken result.

**AI assumption corrected:** the first instinct was to fetch all tasks once
and filter them client-side in JavaScript, since the dataset is small and
it's the least code to write. That was corrected to make search/filtering a
real backend query (`GET /tasks?search=...&status=...`) so it's actually
testable against the API with pytest, and so the frontend and backend can't
silently drift on what "search" means.
