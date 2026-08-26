# My Personal AI Coding Playbook

## When I reach for AI first

- For a new feature, I start with a plan before code. The comments-feature exercise showed me that a generic plan is useful for options, but a repo-grounded plan is what tells me which files, tests, and open decisions matter.
- For code review and security review, I use AI to make a first evidence table, then I check the cited files myself. My manual scan caught the nullable-description issue that the first AI security list missed.
- For debugging, I use AI after I have the exact failing test, error output, and the smallest relevant files. I do not start with a vague “it is broken” prompt.

## When I do not reach for AI

- I pause when the task depends on context I have not inspected. The targeted architecture draft was useful because it said what was not visible instead of guessing.
- I do not use AI to make the final security or scope decision for me; the finding grade and course-scope trade-off stay mine.
- I do not paste real external data, secrets, or anything I am not authorized to share just to get a faster answer.

## My non-negotiables

- I never paste actual `.env` values, credentials, tokens, production configuration, real user/customer data, or unauthorized code into an AI tool.
- I inspect the files behind a claim and record the evidence path before treating the claim as accepted.
- I do not approve a change that reaches beyond the intended files or uses a destructive command without clear permission.

## My review rules

- Before accepting generated backend code, I trace the input, validation, storage update, response, and error path. The `description: null` review taught me to check that model types still match storage and search behavior.
- Before accepting a security finding, I classify it as Valid, False Positive, or Noise using the actual repository evidence and course scope.
- Before accepting a plan or architecture document, I separate facts from assumptions and use targeted anchor files when correctness matters.

## What I am still figuring out

- I am still learning how much context to give: structured context is useful for broad onboarding documents, while targeted context is better for narrow, correctness-sensitive work.
- I am still deciding when a low-severity hardening item belongs in a course backlog versus being recorded for a future production version.
- I will re-read this playbook in 30 days and ask whether I am still following these rules.

## Decision Card

- For a new feature I reach for: Claude Code after I write the feature goal and inspect the affected files. (claude code)
- For a code review I reach for: Codex to produce an evidence-backed review, then I verify the files and tests myself. (codex)
- For debugging I reach for: Claude Code only with the exact failing test or error output and the smallest relevant context. (claude code)
- For infrastructure I reach for: ChatGPT for a first explanation of Docker or CI choices, then I verify the Dockerfile, workflow, and health behavior in the repository. (chatgpt or copilot)
- I will never paste actual `.env` values, credentials, tokens, production configuration, real user/customer data, or unauthorized code into an AI tool.
- My one rule is: I do not accept an AI claim or change until I can point to the files and verification that support it.
