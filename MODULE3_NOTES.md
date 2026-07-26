# Module 3 Notes

Kanban frontend (`frontend/index.html`) on top of the Module 2 backend.

---

## 1. `app/main.py` analysis (read-only, before any Module 3 changes)

Answered directly from the file, before CORS was added:

1. **Framework / app object:** FastAPI. The app instance is `app = FastAPI(...)`.
2. **Routes registered in this file:**
   - `POST /tasks` → `create_task`
   - `GET /tasks` → `list_tasks`
   - `GET /tasks/{task_id}` → `get_task`
   - `PATCH /tasks/{task_id}` → `update_task`
   - `DELETE /tasks/{task_id}` → `delete_task`
   - One additional router is mounted via `app.include_router(health.router)`,
     but its handler function isn't defined in this file, so its name isn't
     guessed here (it's `health_check` in `app/routes/health.py`).
3. **CORS middleware:** not present (at the time of this read).

## 2. Incremental plan — Kanban board

| Step | File/selection | What changes | How I verify it |
|---|---|---|---|
| 1 | `frontend/index.html` (new) | Static 3-column markup, one sample card per column | Open in browser, confirm 3 columns with correct `data-status` and labels |
| 2 | `frontend/index.html` | Repeat the column pattern for InProgress/Done | Visual check + confirm `data-status` values match exactly: `ToDo`/`InProgress`/`Done` |
| 3 | `frontend/index.html` `<script>` | Add `fetchTasks()` / `renderBoard()`, replace sample cards with real data | Start backend, reload, confirm real tasks render sorted High→Medium→Low, id ascending on ties |
| 4 | `frontend/index.html` `<script>` | Add loading/ready/empty/error states | Stop/start backend and reload to force each state, inspect DOM |
| 5 | `app/main.py` | Add CORS middleware | Serve frontend from a different origin, reload, confirm zero console CORS errors |
| 6 | `frontend/index.html` `<script>` | HTML5 drag-and-drop + PATCH + optimistic update/rollback | Drag across columns; force a 422 and a stopped backend, confirm revert both times |
| 7 | `frontend/index.html` (HTML + `<script>`) | Create/edit modal | Create a task, edit a task, confirm validation and all four dismissal paths |

## 3. Incremental plan — create/edit modal

| Flow | Code sections likely affected | Verification step |
|---|---|---|
| New Task opens empty form | New Task button handler, `openCreateModal()` | Click New Task, confirm every field is blank/default |
| Edit opens pre-filled form | Edit button delegation, `openEditModal(task)` | Click Edit on a card, confirm every field matches the card's data |
| Blank title blocked client-side | Form submit handler, title `.trim()` check | Submit with an empty/whitespace title, confirm no network request fires and an inline error shows |
| Create via `POST /tasks` | Form submit handler (create branch) | Submit a valid new task, confirm it appears in the right column |
| Edit via `PATCH /tasks/{id}` | Form submit handler (edit branch) | Edit an existing task, confirm the card updates in place |
| Server 422 shown in modal | Form submit handler catch/error branch | Force an invalid status transition through the form, confirm the modal stays open with the server's message |
| Cancel/Close/Escape/overlay all dismiss | `closeModal()`, four event listeners | Trigger each of the four, confirm the modal closes and errors clear every time |

## 4. CORS

Added proactively (`app/main.py`, `CORSMiddleware`) rather than debugged
reactively, since serving the frontend from a separate static server was
always going to be cross-origin from the backend. Allowed only the local
dev origins actually used (`localhost`/`127.0.0.1` on `5500` and `8080`),
per the prompt's "allow only the local frontend origins I provide"
constraint. Confirmed working live: frontend served via
`python -m http.server 5500`, backend on `8000`, zero CORS errors in the
browser console across the entire verification session below.

## 5. DevTools verification checklist — drag and drop

Checked live in a real browser (not just read from the code) against the
running backend.

| Scenario | What to check | Expected | Result |
|---|---|---|---|
| Valid drag (`ToDo`→`InProgress`) | Network: `PATCH /tasks/{id}` body `{"status":"InProgress"}` → `200` | Card moves and stays; backend reflects the change | **Pass** — confirmed via a follow-up `GET /tasks` |
| Same-column drop | Network: no request fired | Board unchanged, no PATCH sent | **Pass** — DOM identical before/after |
| Invalid transition (`ToDo`→`Done`) | Network: `PATCH` → `422`; UI: toast text | Card reverts to its original column; exact server `detail` message shown | **Pass** — toast showed `Invalid status transition from ToDo to Done. Allowed transitions: [...]` |
| Network failure (backend stopped) | Network: request fails to connect; UI: toast text | Card reverts; generic fallback message (not the 422 message) | **Pass** — reverted, showed "Network error — could not save that move." Note: on this machine the failed fetch took longer than expected to reject (Windows' `localhost` IPv6→IPv4 fallback), so a same-second check can look like it's stuck when it isn't — worth knowing before assuming a bug. |

## 6. 8-item behavior contract

| ID | Behavior | How to check manually | Pass/Fail |
|---|---|---|---|
| 1 | Three status columns render with correct counts | Load the board, compare each column's count badge to its card list | **Pass** |
| 2 | Cards sort by priority inside each column | Create High/Medium/Low tasks in the same column, confirm order | **Pass** |
| 3 | Loading state appears before tasks load | Inspect `#board-status`/`#board` classes immediately after navigation | **Pass** |
| 4 | Empty columns remain visible | Load with zero tasks; confirm 3 columns, `0` counts, "No tasks" placeholders | **Pass** |
| 5 | Error state appears when the backend is stopped | Stop the backend, reload | **Pass** — error banner + Retry shown; Retry recovers once the backend is back |
| 6 | Valid drag sends PATCH and updates the board | Drag `ToDo`→`InProgress`, check board and backend | **Pass** |
| 7 | Invalid drag/server 422 reverts and shows the server message | Drag `ToDo`→`Done` | **Pass** |
| 8 | New Task and Edit modal flows still work, including title validation and dismissal | Create, edit, blank-title block, 422-in-modal, Escape/X/Cancel/overlay | **Pass** — including catching a real bug (below) |

## 7. PATCH edge cases (brainstorm)

Six scenarios not covered by the existing `PATCH /tasks/{id}` tests:

1. PATCH with an empty JSON body `{}` is a no-op that still succeeds.
   Category: malformed | Expected status: 200 | Why it matters: confirms
   `exclude_unset=True` handles "nothing to update" without erroring.
2. PATCH with an invalid priority value (e.g. `"Urgent"`).
   Category: validation | Expected status: 422 | Why it matters: priority
   has no dedicated route-level test, only the enum's implicit coverage.
3. PATCH with an unknown/extra field (e.g. `{"foo": "bar"}`).
   Category: validation | Expected status: 422 | Why it matters: confirms
   `extra="forbid"` is enforced through the live route, not just the model.
4. PATCH title to a blank/whitespace-only value.
   Category: validation | Expected status: 422 | Why it matters: the
   existing PATCH tests never touch title at all.
5. PATCH status to a value that isn't a real status at all (e.g. `"Archived"`).
   Category: validation | Expected status: 422 | Why it matters: distinct
   from an *invalid transition* — this is an invalid enum value entirely.
6. PATCH with multiple fields where one (status) is an invalid transition —
   confirm the whole update is rejected atomically, not partially applied.
   Category: business logic | Expected status: 422 | Why it matters: without
   this check, a rejected status change could silently let other fields
   through.

**Implemented as a real test:** #6, as
`test_patch_invalid_transition_does_not_apply_other_fields` in
`tests/test_tasks.py` — the most valuable of the six, since it tests an
implementation detail (validation order) rather than just a status code.

## 8. Debugging log and reflection

**Debugging log:**
- What I intentionally broke: reordered the `PATCH /tasks/{id}` route in
  `app/main.py` to call `storage.update_task()` *before* validating the
  status transition, to check whether the new atomicity test would actually
  catch it.
- Failing test / summary: `test_patch_invalid_transition_does_not_apply_other_fields`
  failed with `AssertionError: assert 'Updated title' == 'fixture task'` —
  the title got applied even though the transition was still rejected.
- Root-cause diagnosis: the update was written to storage before the
  transition was validated, so an invalid transition still let unrelated
  fields (title) persist; validating first and only writing to storage if
  it passes fixes it.
- Accepted or rejected: accepted — reverting to validate-then-write order
  made the test pass again without touching the test itself, and it's the
  behavior the app is actually supposed to have (an invalid PATCH shouldn't
  partially apply).

**Reflection:**
The AI assistant was most useful during the drag-and-drop and modal work,
where it caught a real bug before I ever ran into it: editing a task
through the modal without touching its status was sending the unchanged
status back to the server, which the same-status business rule then
rejected as a 422 — fixed by only including `status` in the PATCH payload
when it actually changed. Actually running the board in a browser and
inspecting the DOM/network state, rather than trusting the code by
inspection, is what surfaced that bug and also caught a timing false alarm
during the network-failure test (a slow localhost fetch briefly looked like
a stuck rollback but wasn't). The pytest break-test cycle — deliberately
breaking the PATCH route's validation order and watching the exact
assertion fail — was the clearest confirmation that the new edge-case test
was meaningful and not just passing by coincidence. One habit I'll carry
into later modules: verify behavior live, in a browser or a genuinely
failing test, before trusting that a change is correct — two of this
module's real findings only surfaced that way.
