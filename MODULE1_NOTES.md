# Module 1 — End-of-Module Checklist Notes

---

## 1. Reviewed user stories

Role used throughout: **team member** (bc no logged-in users).

| ID | Story | Acceptance Criteria | Notes |
|----|-------|----------------------|-------|
| 1 | As a team member, I want to create a task with a title, description, status, priority, and assignee so that I can track new work. | Title is required; blank or whitespace-only (after trimming) returns HTTP 422 with detail `"Title is required and cannot be blank"`. Description and assignee are optional. Status defaults to `ToDo`, priority defaults to `Medium` when omitted. A created task gets a server-assigned `id` and `created_at`. | **Edge case correction:** blank-title handling. |
| 2 | As a team member, I want to view all tasks in one list so I can see everything that needs to be done. | `GET /tasks` returns every stored task. An empty list returns `[]`, not an error. | |
| 3 | As a team member, I want to filter tasks by status so I can focus on what's still in progress. | `GET /tasks?status=Done` returns only tasks with that exact status. An invalid status value returns 422. | |
| 4 | As a team member, I want to filter tasks by priority so I can see what's most urgent. | `GET /tasks?priority=High` returns only High-priority tasks. Status and priority filters can be combined. | |
| 5 | As a team member, I want to update a task's status so the list reflects real progress. | `PATCH /tasks/{id}` with a `status` field updates only that field. A task in `Done` cannot move back to `ToDo` or `InProgress` — returns 422 with a clear message. Updating a nonexistent id returns 404. | **Scope/edge case correction:** the Done→ToDo/InProgress lock was a rule from the prompt library, not something I'd have added by default — it's a genuine business rule, not scope creep, so it stayed. |
| 6 | As a team member, I want to update a task's title, description, priority, or assignee so I can correct or refine it. | `PATCH /tasks/{id}` is a partial update — only sent fields change. A blank title on update returns the same 422 as creation. An unknown field (e.g. `id`, `created_at`) is rejected with 422, not silently dropped. | **Edge case correction:** unknown-field rejection was added later, after `verify_a.py` exposed that the API silently accepted stray fields. |
| 7 | As a team member, I want to delete a task so the list doesn't accumulate finished or irrelevant work. | `DELETE /tasks/{id}` removes it and returns 204. Deleting a nonexistent id returns 404, not a silent success. | |

---

## 2. Architecture Decision Record

I chose Python + FastAPI + Pydantic with a single JSON file
(`data/tasks.json`) as the storage layer, instead of a real database. The
project is a Module 1 learning exercise, not production software, so the
simplest option that's still testable (Option A from the architecture
comparison) made more sense than adding SQLite/Docker complexity for its own
sake — it's easier to read, debug, and reset by hand while learning, and it
keeps the whole stack to things I already understand well enough to fix
myself. Two assumptions I had to correct along the way: the API originally
accepted any extra field on a request body and let `description` default to
`null`; after checking it against `verify_a.py`, I tightened the Pydantic
models to reject unknown fields (`extra="forbid"`), cap title length at 200
characters, default `description` to `""`, and add a server-only
`created_at` field that clients can't set.

---

## 3. Running skeleton — verified

Confirmed working via automated tests and live manual checks (dates below
are from this session):

- `pytest -v` → **33 passed**, 0 failed (`tests/test_health.py`,
  `test_tasks.py`, `test_models.py`, `test_validators.py`).
- `python tests/verify_a.py` → **8/8 PASS**.
- Live server (`uvicorn app.main:app --port 8001`, verified on a scratch
  port to avoid an already-running process on 8000):
  - `GET /health` → `200`, body `{"status": "ok", "timestamp": "<ISO 8601>"}`.
  - `GET /docs` → `200`, Swagger UI loads.
  - Full CRUD + filter + Done-transition-guard smoke test via curl — all
    behaved as expected.

---

## 4. Reflection log

**Requirements**
- AI got right: pulled the task fields (`id`, `title`, `description`,
  `status`, `priority`, `assignee`) and the Module 1 exclusions (no auth, no
  DB, no deployment) directly from the prompt text without adding anything
  extra.
- Correction: the AI's first pass at scope only captured the high-level CRUD
  requirements from the earliest prompts; the more specific rules — the exact
  422 detail message for a blank title, and the Done→ToDo/InProgress lock —
  were buried in later, more detailed prompts and had to be folded back in
  once the full prompt library was read, rather than being caught up front.
- AI assumption identified: chose `PATCH` for partial updates over a
  full-replace `PUT` without being asked which the project wanted.

**Architecture**
- AI got right: suggested and went with our chosen simplest storage option (JSON file) 
  as per my prompt and the full builds passed all tests and manual checks.
- Correction: `verify_a.py` revealed the initial models were looser than
  intended — no title max-length, extra fields silently accepted, `description`
  defaulting to `None` instead of `""`, and no `created_at` field at all. All
  four were fixed in `app/models.py`, `app/storage.py`, and `app/main.py`.
- AI assumption identified: assumed a simple web frontend was out of scope
  for Module 1, based on the scaffold prompt's explicit exclusion of frontend
  files — flagged this rather than silently building or silently skipping it.

**Scaffold**
- AI got right: all 21 (then 33 after the model changes) automated tests
  passed on the first run, and the live server correctly enforced the
  blank-title, invalid-enum, and Done-status-transition rules under manual
  curl testing.
- Correction: after the first curl smoke test, `data/tasks.json` was left
  holding a leftover test task ("Review ADR") instead of the clean empty seed
  — easy to miss, since the automated tests use an isolated temp file and
  never touch the real one. Had to catch this manually and reset the file
  before it would've been safe to commit.
- AI assumption identified: assumed `kill $!` on a backgrounded Windows
  process would actually stop it. It didn't — Git Bash's job PID didn't match
  the real Windows process, so a stale uvicorn instance kept serving old code
  on port 8000. Had to find and stop the real PID via PowerShell's
  `Get-NetTCPConnection`.
