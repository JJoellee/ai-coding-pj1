# Module 2 Notes

Task Tracker REST API — in-memory storage, business-rule status transitions.

---

## Part A — Data model & storage verification

`app/models.py` (`TaskCreate`, `TaskUpdate`, `TaskResponse`) and
`app/storage.py` (in-memory `_tasks: dict[str, TaskResponse]`) reviewed
against the Prompt A2 checklist before being wired into any routes:

| Check | Result |
|---|---|
| Pydantic v2 syntax only | ✅ `ConfigDict`, `field_validator` — no `@validator`/`class Config` |
| `TaskStatus`/`TaskPriority` are enums, not plain strings | ✅ |
| `TaskCreate`/`TaskUpdate` reject unknown fields | ✅ `extra="forbid"` |
| Title strips whitespace, rejects blank/overlong | ✅ enforced in `_validate_title` |
| `id`/`created_at`/`updated_at` not accepted from client input | ✅ absent from both input models |
| `storage.update_task` uses `model_dump(exclude_unset=True)` | ✅ |
| No routes or database code added in this step | ✅ |

`python tests/verify_a.py` → **8/8 PASS** (whitespace/empty/overlong title,
defaults, extra field, `id`, `created_at`, invalid enum).

One issue caught before it shipped, not by the checklist but by tracing the
update path by hand: the first draft of `TaskUpdate`'s title validator
special-cased `None` as "skip," which meant an explicit `{"title": null}`
would have passed validation and then silently written a `None` title onto
a `TaskResponse` (`storage.update_task` uses `model_copy`, which does not
re-validate). Fixed by removing the `None`-skip and letting `_validate_title`
reject it the same as a blank string — a field validator only runs when the
field is actually present in the request, so omitted fields are still
unaffected.

---

## Part B — Routes, business rules, and manual verification

All five routes (`POST /tasks`, `GET /tasks`, `GET /tasks/{id}`,
`PATCH /tasks/{id}`, `DELETE /tasks/{id}`) added directly to `app/main.py`
per spec, plus `app/business_rules.py` for the status-transition allow-list.

**Transition matrix** (single task, one PATCH per row):

| Step | Transition | Expected | Actual |
|---|---|---|---|
| 1 | ToDo → InProgress | 200 | 200 |
| 2 | InProgress → Done | 200 | 200 |
| 3 | Done → ToDo | 422 | 422 |
| 4 | Done → InProgress | 200 | 200 |
| 5 | InProgress → InProgress | 422 | 422 |
| 6 | InProgress → Done | 200 | 200 |

Pattern `200, 200, 422, 200, 422, 200` matched exactly against the live
server (curl, port 8000).

**Other manual checks against the live server:** invalid-transition detail
message renders correctly (`Invalid status transition from ToDo to Done.
Allowed transitions: [...]`); `PATCH` with no `status` field skips the
transition check and still updates other fields; `GET`/`PATCH` on an unknown
id both return `404` with `Task with id {id} not found`; `DELETE` returns
`204` with a genuinely empty body (`0` bytes); an extra/unknown field on
`POST /tasks` returns `422`.

---

## Automated tests

`pytest -v` → **30 passed**, 0 failed
(`test_health.py`, `test_models.py`, `test_tasks.py`, `test_validators.py`).

**Break test:** temporarily changed `validate_status_transition` to check
only `new` against `{InProgress, Done}` instead of the `(current, new)`
pair — the exact bug named in the course's own debugging checklist ("checks
only the new status, not the pair"). Result: **exactly one test failed**,
`test_patch_invalid_transition_todo_to_done_returns_422` (`assert 200 == 422`),
because the broken version wrongly allowed `ToDo → Done`. Reverted the
change and reran — back to 30/30. This confirms the test suite actually
detects that regression rather than passing by coincidence.

---

## Reflection log

Module 2's data model verification passed 8/8 checks, and the CRUD and
status-transition tests matched the expected `200/200/422/200/422/200`
pattern on the first run, with all 30 pytest tests passing. To confirm the
test suite would actually catch regressions, I broke the transition check so
it validated only the new status instead of the `(current, new)` pair —
exactly one test failed, as expected. The main thing I verified carefully
was that Module 2's transition rules invert part of Module 1's
(`Done → InProgress` goes from forbidden to allowed), so I tested the exact
rule table rather than assuming it was purely additive.
