# Technical Decision Note: Dockerfile Design

**Status:** Rewritten in my own words (Trade-offs, Open Questions) after
the AI-drafted version.

## Context

Module 4 added a way to run the Task Tracker backend as a container,
without adding a database, authentication, or an actual deployment target.
Before this, the app only ran via `uvicorn app.main:app --reload` directly
on a developer's machine, with dependencies installed into a local venv.
That's fine for course work but doesn't demonstrate — or prove — that the
app can run in an isolated, reproducible environment with a locked-down
runtime user, which is a normal expectation before an app goes anywhere
near a real deployment (even though this project still isn't deploying
anywhere). The immediate trigger was `D1`/`D2` in this module's prompt
sequence, which specified concrete constraints (multi-stage, non-root,
`python:3.11-slim`, no `--reload`) rather than leaving the design open.

## Decision

Use a two-stage `Dockerfile`:

1. A `builder` stage (`python:3.11-slim`) that only installs dependencies
   from `requirements.txt` via `pip install --user`, producing an isolated
   `/root/.local` directory.
2. A runtime stage (also `python:3.11-slim`, not `latest`) that creates a
   non-root user named `app`, copies only the installed packages and the
   `app/` package itself (not `tests/`, `docs/`, `frontend/`, `data/`, or
   any `.env` file) from the builder stage, sets `USER app` before `CMD`,
   and runs `uvicorn app.main:app --host 0.0.0.0 --port 8000` with no
   `--reload`.

`.dockerignore` excludes `.env`, `.git/`, virtual environments, caches, and
OS/editor cruft from the build context entirely, independent of what the
`Dockerfile` explicitly copies.

This was built and verified for real on 2026-08-26: `docker build` (13/13
steps, no errors), `docker run` + `curl /health` → `200` with the expected
JSON body, `docker exec tt-dev whoami` → `app`, and `docker history` shows
no `python:latest` reference or secret-bearing layer.

## Alternatives Considered

- **Single-stage build** (just `FROM python:3.11-slim`, `pip install`,
  `COPY . .`, done). Simpler, fewer lines. Rejected in favor of
  multi-stage because a single stage would either need build tools
  present in the final image (larger, more attack surface) or risk
  copying more of the repo than the runtime needs (`tests/`, `.git/`,
  `venv/`) if the `COPY` instruction were ever loosened to `COPY . .`
  later — the two-stage split makes "only ship what runtime needs"
  structural, not just a habit to remember.
- **`python:3.11-alpine`** instead of `-slim`. Smaller image, and
  originally rejected preemptively on Alpine's musl-libc reputation for
  breaking C-extension wheels — **tested for real on 2026-08-26, and that
  reputation didn't hold for this project's actual dependencies.** A
  build using `python:3.11-alpine` for both stages completed cleanly;
  `pip install --user -r requirements.txt` found prebuilt `musllinux`
  wheels for every compiled package in the tree (`pydantic-core`,
  `httptools`, `uvloop`, `pyyaml`, `watchfiles`, `websockets`) — no
  compilation from source, no missing build tools. Still stayed with
  `-slim`, but now for a real reason instead of a guessed one: the test
  Dockerfile needed `adduser -D -s /sbin/nologin` instead of `useradd`
  (Alpine has no `useradd`), which is a small but real syntax cost, and
  the *build* succeeding doesn't confirm the *running* container behaves
  identically — that image was never `docker run` + `curl`'d. Swapping
  base images now would mean re-verifying everything in this note's
  Context section from scratch for a size optimization nobody asked for.
- **Running as root** (skip the `useradd`/`USER app` steps entirely).
  Simplest possible option. Rejected outright — this was an explicit,
  non-negotiable constraint (`D1`: "Create a non-root user," "Switch to
  USER app before CMD"), not just a nice-to-have.
- **`docker-compose.yml`** for a one-command run. Would be convenient, but
  out of scope — `D1` only asked for a `Dockerfile` and `.dockerignore`,
  and adding compose now would be scope creep beyond what this module
  actually specified.

## Trade-offs

Multi-stage does mean the `Dockerfile` is longer than it strictly needs to
be, and if someone hasn't seen the pattern before I'd have to explain why
there are two `FROM` lines. Worth it though — the alternative was trusting
myself (or whoever edits this file later) to never accidentally change
`COPY app/ ./app/` into a lazy `COPY . .` and drag in `venv/` or `tests/`
with it. I'd rather the structure make that mistake impossible than rely
on remembering not to make it.

Pinning `python:3.11-slim` exactly is going to bite me eventually — I'll
have to remember to bump it by hand for patch releases instead of getting
them for free. I'm fine with that trade. I'd rather know precisely what
I'm running than have a `latest` tag quietly change under me between
builds with no changelog to point to.

The `pip install --user` + copy-`/root/.local` trick is a little unusual
if you're expecting a proper virtualenv inside the builder stage. It
works, and it's fewer lines than setting up a venv would be, but I'll
admit it's not the first pattern most Docker tutorials show, so a reviewer
unfamiliar with it might raise an eyebrow before checking that it's fine.

## Consequences

- The image only runs the backend API — there is still no way to serve
  `frontend/index.html` from the same container; it stays a separate
  static-file-server concern, unchanged by this decision.
- Because storage is in-memory (a Module 2 decision, not this one),
  stopping the container discards all data — same behavior as restarting
  the bare `uvicorn` process locally, just easier to forget when a
  container feels more like a "deployed thing."
- Anyone extending this later (e.g., actually deploying it) inherits a
  non-root, slim, reasonably minimal base to build from, rather than
  having to retrofit those constraints onto a root-run single-stage image.

## Update: HEALTHCHECK added

Decided this one instead of leaving it open — added
`HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3`
hitting `GET /health` via `python -c "import urllib.request; ..."` rather
than `curl`, since `python:3.11-slim` doesn't have `curl` installed and
adding it just for a health probe felt like the wrong trade (`urllib` is
already in the stdlib, so this costs nothing extra in the image).
**Confirmed live on 2026-08-26:** rebuilt, ran, and
`docker inspect --format='{{.State.Health.Status}}' tt-dev` printed
`healthy` after the start period.

## Update: alpine benchmarked

Also closed out for real on 2026-08-26 (see the Alternatives section
above for the full result) — built a test image on `python:3.11-alpine`
and it succeeded, prebuilt wheels and all. The musl-libc concern that
drove the original `-slim` choice turned out to be reputation, not a
property of this project's actual dependencies. Stuck with `-slim` anyway,
but for the syntax-cost and runtime-unverified reasons noted above, not
because alpine was assumed broken.

## Open Questions

Whether the alpine build's *running* container actually behaves
identically to `-slim` is still open — the test build was never
`docker run` + `curl`'d, only built. That's the next thing to check if
image size ever actually becomes a real constraint here, rather than a
hypothetical one.

I would do this differently by deciding up front whether this Dockerfile
is meant to stay a local-only convenience or is step one toward a real
deployment target — I never actually answered that question, and it would
have focused which of these trade-offs were worth spending time on versus
which were premature (the alpine benchmark turned out to be worth doing;
`docker-compose.yml`, rejected above as scope creep, might not have been
if the answer were "yes, this is heading toward deployment").
