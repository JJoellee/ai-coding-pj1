# Final AI Review and Ownership Evidence

## AGENTS.md guardrails

- Repo-specific stack and commands included: **yes** (`AGENTS.md` §§1-3:
  exact tech stack with versions, exact run command, exact test command
  including the `pytest.ini` gotcha).
- Docs-first/read-first guardrail included: **yes** — added during this
  final-project pass (`AGENTS.md`, "Read-first guardrail" section):
  read the actual current file before editing or claiming behavior, and
  treat the code as the source of truth over any doc, including this one.
- Unexpected app/frontend edits rule included: **yes** — also strengthened
  during this pass (`AGENTS.md` §7): `app/`/`frontend/` are explicitly
  called protected, restricted to small bug/security/doc-correction fixes,
  with an explicit pointer to explain any such change right here.

## AI code review mini-log

Reviewed diff: the bug fix made during this final-project pass
(`app/models.py` + `tests/test_tasks.py` — the `TaskUpdate` null-handling
fix described below).

| AI comment | Grade: Useful / Noise / Wrong | Reason | Verification or decision |
|---|---|---|---|
| `description`'s validator coerces `null`→`""`, while `status`/`priority` reject `null` outright (422) — inconsistent behavior across sibling fields on the same model. | Noise | The asymmetry is intentional: `description` has a sensible empty-string default; `status`/`priority` don't (a task can't meaningfully have no status). Both docstrings state this explicitly. | Re-read both validators' docstrings; confirmed the reasoning is deliberate, not an oversight. No change made. |
| The same null-check pattern should also be added to `TaskCreate.description` for consistency. | Wrong | `TaskCreate` doesn't need it — `storage.add_task` already does `payload.description or ""` at construction time, a different mechanism with the same effect. Adding a validator there would duplicate protection that already exists. | Read `storage.add_task`; confirmed the `or ""` coalescing is already present on that path. No change made. |
| The new regression test uses inline `#` comments instead of a docstring, inconsistent with the rest of the test suite. | Useful | Checked — genuinely true, no other test function in `tests/test_tasks.py` has a comment or docstring. | Kept the comment anyway as a deliberate exception: this specific test's rationale (a real security-review finding, plus a non-obvious short-circuit-masking detail) is exactly the kind of "why" worth writing down. Acknowledged and downgraded from "fix it" to "deliberate, documented exception." |
| The fix didn't check whether `assignee` or `due_date` have the same class of bug. | Useful — and acted on | Real gap in the first pass. | Checked: `TaskResponse.assignee: Optional[str]` and `TaskResponse.due_date: Optional[date]` are both already `Optional`, so `null` is legitimate for them — no bug exists there. Confirmed by re-reading `TaskResponse`'s field declarations. No change needed, but this was verified, not assumed. |

## AI security mini-review

Full review in [`docs/security-review.md`](security-review.md) (Module 5,
Codex, read-only static review — no app started, no tests run). Summary of
the AI-generated findings and their grades:

| Finding | File evidence | Grade: Valid / False Positive / Noise | Reason | Next action |
|---|---|---|---|---|
| S-01: No authentication protects task CRUD operations | `app/main.py:38-186`; `AGENTS.md` states auth is out of course scope | Valid | Real, but intentional course scope, not a course-stage defect. | Keep API local-only for the course; would need real auth before any deployment. |
| S-02: `description`/`assignee` have no length limits; tasks stay in process memory | `app/models.py` (title has a 200-char limit, description/assignee don't); `app/storage.py` (in-memory dict) | Valid | Real, low severity for a local/course-only API. | Deferred — proportionate field limits if deployment scope ever changes. |
| S-03: GitHub Actions use mutable major-version tags (`@v4`, `@v5`), not pinned SHAs | `.github/workflows/ci.yml:11-15` | Valid | Real supply-chain hardening gap, but low priority — hardening, not an observed failure. | Deferred — ranked lowest in the backlog; not acted on this pass. |

## Manual security check

I didn't just copy the AI security review's findings — I reproduced the
one that mattered most (H-03) against the real running app before trusting
it, and in doing so found the AI review's finding was **incomplete**, not
just correct.

`docs/security-review.md`'s manual-scan finding H-03 claimed `PATCH
{"description": null}` could break `TaskResponse`'s type contract. I
reproduced this for real:

```
PATCH /tasks/{id} {"description": null}  ->  200, stores description=None
GET /tasks?search=<term not matching the title>  ->  500 Internal Server Error
```

Confirmed exactly as claimed. But H-03 only names `description`. Before
fixing it, I checked whether the same class of bug — an `Optional` field on
`TaskUpdate` whose `TaskResponse` counterpart is *not* `Optional` — affected
anything else on the same model. It did: `PATCH {"status": null}` and
`PATCH {"priority": null}` both silently corrupted a task the same way,
and `status: null` is worse than `description`'s case — the business-rule
error-message formatting calls `.value` on the current status, so a
corrupted task would crash *any future transition attempt on it too*.
Neither the AI security review nor the AI code-review pass caught this;
it came from manually enumerating every `Optional` field on `TaskUpdate`
against its `TaskResponse` counterpart after the first bug was confirmed,
not from re-reading AI output more carefully.

## One AI output I corrected

`docs/security-review.md` (Module 5, Codex) correctly identified the
`description: null` bug (H-03) but stopped there — it didn't check
sibling fields for the same bug class. I corrected this by extending the
fix and the investigation to `status` and `priority`, which turned out to
have the same root cause and, for `status`, a worse consequence. I didn't
reject the AI's finding — it was accurate as far as it went — but treating
"AI found one instance of a bug class" as "the bug class is now fully
handled" would have shipped two more crash paths.

## Three AI usage rules

1. **Never paste:** real `.env` values, credentials, tokens, production
   logs, or real personal/customer data — into this repo or into any AI
   tool while working in it.
2. **Always verify:** reproduce a claimed bug, finding, or behavior against
   the real running app or test suite before acting on it or writing it
   down — an AI's word alone (including this session's) is not evidence.
3. **Record AI contributions by:** naming the specific tool, the exact
   file(s) touched, the evidence checked, and the accept/correct/reject
   decision — in `docs/`, not left implicit in chat history that won't
   ship with the repo.

## Ownership statement

I'm comfortable submitting this repo because every claim in it that
matters — the CI green→red→green cycle, the Docker build/run/health/
non-root checks, the security findings, and the bug described above — was
independently reproduced against the real app or a real API before being
written down, not accepted because an AI tool said so. The one real bug
found this pass wasn't just copied from the security review; I verified it
end to end, then found it was bigger than reported and fixed the full
scope, with a break-tested regression test for each of the three affected
fields. `app/` and `frontend/` are otherwise untouched this module, exactly
as the ground rules require. Across Modules 1–3, ChatGPT handled the
earliest planning and user-story draft; GitHub Copilot supplied inline help
while writing the due-date/overdue model work and storage search filter;
Cursor consolidated repeated frontend DOM lookups into `formFields`; Codex
drafted the due-date and search-filter pytest files; and Claude performed
live browser/network verification and break-tests. Module 4 used Claude
Code, and Module 5 used Codex for the security, governance, architecture,
and final-review work. I can explain the reasoning behind every file this
final pass changed — the models.py fix, the two new docs, the README
section, and the AGENTS.md/CLAUDE.md guardrail additions — without deferring
to "the AI suggested it."
