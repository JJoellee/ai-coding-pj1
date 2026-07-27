# Verification — Mid-Course Project

## Baseline check

Before any changes, on `main` (commit `72526db`, "Module 3: add frontend"),
branch `mid-course-project` created from that point:

```
pytest -v
============================= 31 passed in 0.61s ==============================
```

31/31 passing, 0 failures — clean baseline to build on.

## Backend test results (after both features)

```
pytest -v
============================= 42 passed in 0.22s ==============================
```

42/42 passing — the 31 baseline tests, unmodified, plus 11 new tests:

- `tests/test_due_dates.py` (6 tests): valid due date on create, invalid
  date format → 422, overdue detection, Done-task-with-past-due-date is
  never overdue, update due date, `overdue=true` filter returns only
  overdue tasks.
- `tests/test_search_filters.py` (5 tests): search matches title, search
  matches description, search combined with status + priority, no matches
  → 200 `[]`, invalid status filter value → 422.

That's 11 new tests against the brief's minimum of 4.

## Manual browser checks

Both servers run locally (`uvicorn` on `8000`, `python -m http.server 5500`
for the frontend), checked live via automated browser interaction — DOM
state, network requests, and console — not just by reading the code.

| Check | Result |
|---|---|
| Overdue pill appears only for tasks with a past due date and status ≠ Done | **Pass** — a Done task with a past due date correctly showed no pill |
| Priority sort unaffected by adding due dates | **Pass** — cards still sorted High → Medium → Low |
| "Overdue only" checkbox filters the board via a real `GET /tasks?overdue=true` request | **Pass** — confirmed in the network log, not just the DOM |
| Search box (debounced) filters via `GET /tasks?search=...` | **Pass** — request fired ~300ms after typing stopped, not per keystroke |
| Priority dropdown filter combines correctly with other active filters | **Pass** |
| "Clear filters" resets all inputs and refetches the unfiltered list | **Pass** |
| Create a task with a due date through the modal | **Pass** — card showed the correct due date immediately |
| Edit a task to clear its due date | **Pass** — due-date line disappeared from the card after save |
| Requests are genuine backend queries, not client-side filtering | **Pass** — network log showed `?overdue=true`, `?search=memo`, `?priority=High` as actual outgoing requests |

## Behavior contract before/after refactor

**Refactor performed:** `frontend/index.html`'s modal functions
(`openCreateModal`, `openEditModal`, the form submit handler) each called
`document.getElementById("field-...")` repeatedly for the same six fields
every time they ran, instead of caching references once like the rest of
the script already does (`boardEl`, `modalOverlay`, etc.). Consolidated
into a single `formFields` object cached at startup; all six functions now
reference `formFields.title`, `formFields.dueDate`, etc. Purely mechanical
— no behavior was intended to change.

| Behavior | Before refactor | After refactor |
|---|---|---|
| Backend test suite | 42/42 passing | 42/42 passing (unaffected — frontend-only change) |
| Create task with title, due date, assignee via modal | Card appears with correct due date and assignee | **Pass** — identical |
| Edit modal pre-fills title/due-date/assignee correctly | Pre-fill matches the card's data | **Pass** — identical |
| Editing and saving applies the change | Card updates in place | **Pass** — identical |

No behavior changed; the refactor only removed duplicate DOM lookups.

## Break-test evidence

Two break-tests, one per feature, each following: predict the break →
introduce it → run the affected test → observe the exact predicted failure
→ revert → confirm the full suite is green again.

### Break-test 1 — Feature 1 (Done tasks are never overdue)

**Break:** in `app/models.py`, changed
`if due_date is None or status == TaskStatus.DONE: return False` to
`if due_date is None: return False` — dropping the Done-status exception.

**Result:**
```
tests/test_due_dates.py::test_done_task_with_past_due_date_is_not_overdue FAILED
AssertionError: assert True is False
```
Exactly the predicted failure — only that one test failed; the other five
due-date tests still passed, confirming the test is precisely targeted at
this one rule.

**Reverted**, full suite back to 42/42.

### Break-test 2 — Feature 2 (search composes with other filters)

**Break:** in `app/storage.py`, changed the `search` filter to run against
`_tasks.values()` (the full unfiltered dict) instead of the already
status/priority/assignee/overdue-filtered `tasks` list — so search would
silently ignore every other active filter.

**Result:**
```
tests/test_search_filters.py::test_search_combined_with_status_and_priority FAILED
AssertionError: assert 2 == 1
```
Predicted and confirmed: the combined-filter test returned both the
matching task *and* an unrelated task that only matched on `search`,
proving the combined-AND behavior was genuinely broken and the test catches
it. The other four search tests still passed (they don't combine filters,
so the bug didn't affect them).

**Reverted**, full suite back to 42/42.
