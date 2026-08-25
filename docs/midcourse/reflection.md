# Reflection — Mid-Course Project

I used ChatGPT for the earliest planning pass — turning the brief into two
scoped features and a first draft of the user stories — since that's the
kind of open-ended brainstorming a general chat assistant is well suited
to. GitHub Copilot handled the moment-to-moment inline suggestions while
writing the `due_date`/`is_overdue` model code and the `search` filter in
`storage.py`, the small stuff like completing a Pydantic field declaration
or a list comprehension. Cursor did the larger multi-file edit when the
modal's repeated `document.getElementById` calls got consolidated into a
single cached `formFields` object across three functions at once. Codex
generated the first draft of the new pytest files,
`test_due_dates.py` and `test_search_filters.py`, from the feature
descriptions. Claude did the live verification work — actually running the
app in a browser, checking DOM state and network requests, and the two
break-tests — since that part needed a tool that could drive the app, not
just write code.

One moment AI helped: when asked to decide, before writing any code,
whether "overdue" should be computed or stored, the first instinct was to
store it — matching the existing pattern for `created_at`/`updated_at` —
before catching that a stored flag would go stale the moment a due date
passed with no edit touching that task. That's a subtle correctness bug
that's easy to miss when focused on "does the feature work" rather than
"is the rule actually right."

One moment it slowed things down: reconciling suggestions from different
tools that assumed slightly different conventions — one favored a
`due_date` filter as a separate endpoint, another assumed client-side
filtering of an already-fetched list. Neither matched the existing
`GET /tasks` query-param pattern already established for `status`/
`priority`, so both had to be corrected back to that convention before
anything was accepted.

One place review changed the result: after both features passed their
tests once, pushing for genuine break-tests — actually breaking
`is_task_overdue` and the combined-filter logic in the source, rerunning
pytest, and watching the exact predicted assertion fail before reverting —
confirmed two of the new tests were watertight rather than just passing by
coincidence.

Habit kept from this: a passing test or a rendered page isn't proof by
itself. Break the thing the test claims to check, and confirm it fails for
the right reason, before trusting it.
