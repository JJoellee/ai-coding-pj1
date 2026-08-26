# Governance Retrospective - AI-Assisted Coding

## Basis and limits

This worksheet uses the Module 5 risk rubric supplied in the course prompt,
the repository evidence reviewed for `docs/security-review.md`, and the
attached worksheet template. It records a course toy project. No actual `.env`
file, production credentials, or real external user/customer data was observed
in the review.

## What I Shared With AI

| Item | Module | Risk level | Reason |
|---|---:|---|---|
| Task Tracker code | 2-5 | Low | This is course toy-project code; the reviewed repository contains no observed secrets, real user data, or proprietary production logic. |
| Test output and stack traces | 2-4 | Low | The reviewed test material concerns the course project and contains no observed credentials, tokens, or real user data. |
| Frontend code | 3 | Low | The single-file frontend is course project code and uses a local backend address. |
| Dockerfile and CI YAML | 4 | Low | The inspected Docker and CI configuration contains no observed secrets or production deployment configuration. |
| Any real external data used by mistake | Not used | Not applicable - would be High if present | No real external data was observed in the review. Real customer/user data, credentials, or unauthorized code would be High risk and must not be pasted. |

## What I Received From AI

| Generated thing | Module | Do I understand it line by line? | Action |
|---|---:|---|---|
| Backend models and validators | 2 | Partly | Trace inputs, validation, and outputs against the models and tests before accepting changes. |
| Frontend board and drag-and-drop logic | 3 | Partly | Review the move, save, and error paths before accepting UI behavior. |
| CI workflow | 4 | Partly | Read each workflow step and confirm which command it runs; record CI hardening decisions separately. |
| Dockerfile | 4 | Partly | Explain the build stages, non-root user, and health check before accepting future changes. |
| Security findings and plans | 5 | Partly | Check each claim against file evidence, keep the final judgment mine, and record accepted or rejected findings. |

## 5.3A - Classification notes

- The reviewed material is Low risk because it is a course toy project with no
  observed sensitive data or production secrets.
- Real external data, credentials, tokens, `.env` values, or code I am not
  authorized to share are High risk and must not be pasted into an AI tool.
- A future private repository without secrets or personal data should be treated
  as Medium risk until its sharing permission is confirmed.

## 5.3B - Trace of the status-transition block

Source: `app/business_rules.py:29-34`.

| Line(s) | What it does | Why it is there | What could break | Do I own this yet? |
|---|---|---|---|---|
| 29 | Checks whether the requested `(current, new)` status pair is absent from `VALID_TRANSITIONS`. | Statuses are valid individually, but the task workflow only permits specific moves. Checking the pair enforces the workflow. | Removing it would allow disallowed moves such as `ToDo` to `Done` or a status changing to itself. Changing the pair check could reject valid moves or allow invalid ones. | Partly - I can explain the rule and should verify each allowed pair in the tests. |
| 30 | Builds text such as `ToDo->InProgress` for every allowed pair, then sorts it. | The error message can tell a client which moves are permitted. Sorting makes the list deterministic instead of depending on set iteration order. | Without it, invalid requests would have a less useful explanation. Removing `sorted` would not change the rule, but the message order could vary. | Partly - I understand the output; I should re-read the set comprehension and enum `.value` access. |
| 31-34 | Raises FastAPI's `HTTPException` with HTTP 422 and a detailed message. | Raising the exception stops the update before storage changes occur and returns a client-error response for an invalid transition. | If it were removed, the validator would return normally and the caller could continue with an invalid update. Using the wrong status code or omitting the detail would make API behavior less clear or inconsistent. | Partly - I understand the intent and should verify the 422 behavior with the route tests. |

Assumptions to verify: `current` and `new` are `TaskStatus` values, and the
route calls this validator before writing an update. The first assumption is
declared in `app/business_rules.py`; the route call is visible in
`app/main.py:156-160`.

## Notes for 5.3C

- I shared only course-project code, test output, frontend code, Docker/CI
  configuration, and security-review material in this work. No actual `.env`
  file, credentials, tokens, production configuration, real user/customer data,
  or unauthorized code was observed.
- I will not paste real external data, secrets, `.env` values, or code that I
  am not authorized to share.
- Before I accept generated code or a security finding, I will trace its inputs,
  validation, outputs, and error path against the surrounding files and tests.
- For a generated finding or change, I will record the module, the files or
  lines involved, the evidence I checked, and whether I accepted, changed, or
  rejected it and why.

## 5.3C - Concrete personal AI usage rules

| Rule category | Draft rule | Evidence from my notes | What is still vague? | Revised rule |
|---|---|---|---|---|
| What I will never paste | I will not paste sensitive information. | Notes identify real external data, secrets, `.env` values, and unauthorized code as excluded. | “Sensitive information” is too broad to audit. | I will never paste real external data, credentials, tokens, `.env` values, production configuration, real user/customer data, or code I am not authorized to share. |
| What I will always verify before accepting | I will verify AI output. | Notes require tracing inputs, validation, outputs, and error paths against surrounding files and tests. | “Verify” needs a repeatable checklist. | Before accepting generated code or a security finding, I will trace its inputs, validation, outputs, and error path against the relevant surrounding files and tests. |
| How I will record AI contributions | I will document AI work. | Notes require module, files/lines, checked evidence, and the decision with its reason. | The record location and decision states must be explicit. | For each generated finding or change, I will add a documentation record with the module, affected files or lines, evidence checked, and a decision of accepted, changed, or rejected with the reason. |
