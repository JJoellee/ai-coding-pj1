# Module 5 Security Review

## Scope and method

This was a read-only review. No application was started, no tests were run,
and no files outside this document were modified. Findings are based on static
inspection of the repository and should not be read as evidence that an issue
has been exploited in a deployed environment.

Files reviewed included `app/main.py`, `app/models.py`, `app/storage.py`,
`app/business_rules.py`, `app/validators.py`, `app/routes/health.py`,
`frontend/index.html`, `tests/`, `requirements.txt`, `Dockerfile`,
`.dockerignore`, `.env.example`, `AGENTS.md`, and `.github/workflows/ci.yml`.

## AI finding grades

| Finding ID | Proposed grade | Reason | Evidence used | Student decision to confirm |
|---|---|---|---|---|
| S-01 | Valid | The lack of authentication is real. It is intentional course scope rather than an immediate course defect, but would be a production risk if the API were exposed. | `app/main.py:38-186` registers unrestricted task CRUD routes. `AGENTS.md` states that authentication is not to be added for the course scope. | Keep as a scope-limited production risk, not a request to add auth now. |
| S-02 | Valid | `description` and `assignee` have no visible length limits, while created tasks remain in process memory. The stated Low severity is appropriately cautious. | `app/models.py:20-26` limits title length, while `app/models.py:55-59` does not set equivalent limits for `description` or `assignee`; `app/storage.py:14-43` retains tasks in `_tasks`. | Keep Low, or classify as Noise only if trusted local callers are guaranteed. |
| S-03 | Valid | Mutable GitHub Action tags are a specific CI supply-chain hardening concern. The finding does not claim a compromise and retains Low severity. | `.github/workflows/ci.yml:11-15` uses `actions/checkout@v4` and `actions/setup-python@v5`. | Keep as a low-priority DevOps hardening item. |

## Manual scan findings

| ID | Finding | Evidence |
|---|---|---|
| H-01 | No authentication or authorization protects task CRUD operations. This is intentional course scope, but a production exposure risk. | `app/main.py:38-186`; `AGENTS.md` course instructions. |
| H-02 | `description` and `assignee` have no visible length limits, and tasks accumulate in memory. This is a low-severity resource-consumption concern if untrusted clients can reach the API. | `app/models.py:55-59`; `app/storage.py:14-43`. |
| H-03 | A `PATCH` with `"description": null` can break the stored task type invariant: updates accept a nullable description, but `TaskResponse` requires a string. The storage update uses `model_copy(update=...)`, which does not validate update data; search then calls `.lower()` on the description. This is a low-severity availability risk from untrusted input. | `app/models.py:83-88`, `app/models.py:117-120`; `app/storage.py:84-91`, `app/storage.py:129-131`. Pydantic's `model_copy(update=...)` documentation states that update data is not validated. |

## Reconciliation

| Agreement | AI-only | You-only |
|---|---|---|
| S-01 / H-01: No authentication or authorization; intentional course scope but production risk. | S-03: GitHub Actions use mutable major-version tags rather than immutable commit SHAs. | H-03: A nullable update can violate the response model's `description: str` invariant and cause an availability failure during search. |
| S-02 / H-02: Unbounded `description` and `assignee` values accumulate in memory. | — | — |

AI identified broad exposure, CI hardening, and input-size concerns.
The manual scan added a type-invariant flaw at the model-to-storage boundary.

## Prioritized backlog

| Rank | Finding | Why it matters | Suggested owner | Next action |
|---|---|---|---|---|
| 1 | No authentication or authorization | Any client that can reach the API can access and mutate all tasks. | Course/project owner | Keep the API local-only for the course; define authentication and authorization requirements before deployment. |
| 2 | Nullable `description` update breaks the type invariant | A crafted valid request can leave stored data incompatible with response and search behavior. | Backend | Add a regression test, then make `description` consistently nullable or normalize it to a string on update. |
| 3 | Unbounded `description` and `assignee` | Repeated oversized requests can increase memory use in the in-memory store. | Backend | Apply proportionate field limits; consider request-size and rate limits if deployment scope changes. |

The CI action pinning finding remains Valid but ranks fourth because it is hardening work, not an observed application-level failure.

## Review limits

- No runtime, dependency-vulnerability, container, or external deployment scan was performed.
- Git history, CI secrets, hosting configuration, and runtime environment variables were not inspected.
- No actual `.env` file was present in the repository root during this review; only `.env.example` was inspected.
