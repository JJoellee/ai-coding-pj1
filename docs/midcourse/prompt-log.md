# Prompt Log — Mid-Course Project

Six meaningful prompts that drove this work, three per feature, including
one weak → strong rewrite. "AI response" is what was produced; "Accepted /
edited / rejected" is the actual decision that made it into the code.

---

## Feature 1: Due dates + overdue

### Prompt 1 (weak → strong rewrite)

**Weak:** "Add due dates to tasks."

**Strong (rewritten):** "Add an optional `due_date` field (ISO date,
`YYYY-MM-DD`) to `TaskCreate`, `TaskUpdate`, and `TaskResponse`. Reject
invalid date formats with 422 via Pydantic's own date parsing — don't
hand-write format validation. Don't add a due-date-only endpoint; reuse the
existing create/update routes."

**AI response:** added `due_date: Optional[date] = None` to all three
models; relied on Pydantic's built-in `date` type to reject malformed input
automatically, with zero custom validation code.

**Accepted / edited / rejected:** Accepted as-is. The weak version would
have produced *something*, but without the "reuse existing routes" and
"use Pydantic's own parsing" constraints it likely would have added a
redundant hand-rolled date-format check or a new endpoint neither of which
was needed.

### Prompt 2

"Decide whether `is_overdue` should be computed or stored, and justify the
choice before writing code. A task is overdue if it has a due date in the
past; decide what happens for `Done` tasks."

**AI response:** proposed computing `is_overdue` as a Pydantic
`@computed_field` on `TaskResponse` (never stored), with the rule
`due_date < today() and status != Done`.

**Accepted / edited / rejected:** Accepted — but this is also where the
corrected assumption happened (see `docs/midcourse/user-stories.md`). The
very first draft nearly stored it as a persisted flag before the staleness
problem was reasoned through and the design changed to computed-on-read.

### Prompt 3

"Add an `overdue` query filter to `GET /tasks`, using the exact same
overdue rule as the computed field — don't duplicate the logic."

**AI response:** extracted the rule into a standalone
`is_task_overdue(due_date, status)` function in `app/models.py`, used by
both the computed field and `storage.get_all_tasks(overdue=...)`.

**Accepted / edited / rejected:** Accepted — a deliberate refactor-before-
duplicating move, so the "what counts as overdue" rule exists in exactly
one place.

---

## Feature 2: Search + combined filters

### Prompt 4

"Extend `GET /tasks` with an optional `search` query parameter that does a
case-insensitive substring match against `title` OR `description`. It must
compose with the existing `status`/`priority` filters via AND, not replace
them. No matches must return 200 and `[]`, never 404."

**AI response:** added `search: Optional[str] = None` to
`storage.get_all_tasks`, applied after the status/priority/assignee/overdue
filters in sequence, so it narrows whatever's already been filtered rather
than the full list.

**Accepted / edited / rejected:** Accepted, then verified with a break-test
(see `docs/midcourse/verification.md`) that search genuinely composes with
the other filters instead of silently overriding them.

### Prompt 5

"Add a filter bar to the frontend that actually calls the new backend query
params — don't filter the already-fetched `tasks` array in JavaScript."

**AI response:** added a filter bar (search input, status/priority selects,
overdue checkbox, clear button) that rebuilds a query string and calls
`fetchTasks()` on every change, with the search input debounced 300ms so it
doesn't fire a request per keystroke.

**Accepted / edited / rejected:** Accepted as designed. Confirmed via the
Network tab (not just by reading the code) that the requests sent were
`GET /tasks?search=...`, `?overdue=true`, `?priority=High`, etc. — real
backend queries, not decoration.

### Prompt 6

"Verify the invalid-filter-value contract: an unrecognized `status` value
on `GET /tasks` must 422, not silently return an empty list."

**AI response:** confirmed this already worked for free — FastAPI validates
`status: TaskStatus | None` against the enum before the route body even
runs — and flagged that no existing test checked this specifically on the
list route (only on create/update).

**Accepted / edited / rejected:** Accepted; added
`test_list_tasks_invalid_status_filter_returns_422` to close the gap.
