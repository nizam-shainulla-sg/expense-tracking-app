---
description: Write tests for a spec via the test-writer subagent, then run them via the test-runner subagent, and report results.
argument-hint: <spec file path under docs/specs/, or pasted spec text>
allowed-tools: Agent, Read, Write, Bash, Glob
model: inherit
---

Input spec: $ARGUMENTS

Do the following in order. Do not skip the handoff between agents — this command exists specifically to keep writing and running separated.

1. **Resolve the spec.** If `$ARGUMENTS` looks like a path, read it (try it as given, then under `docs/specs/` if it doesn't resolve). If no path is given or it doesn't exist, treat `$ARGUMENTS` itself as the spec text. If you truly have no spec content to work with, stop and ask the user for one rather than guessing at requirements.

2. **Dispatch to `test-writer`.** Call the Agent tool with `subagent_type: "test-writer"`. In the prompt, include the full spec content (not just its path — the agent starts with no context) and ask it to add the corresponding tests to `expenses/tests.py`, following the project conventions it already knows (seeded demo users, `Decimal` amounts, named routes via `reverse()`, etc.). Wait for it to finish and note exactly which test classes/methods it added.

3. **Dispatch to `test-runner`.** Call the Agent tool with `subagent_type: "test-runner"`. In the prompt, name the specific test classes/methods `test-writer` just added (so it can run them targeted, e.g. `.django_venv/bin/python manage.py test expenses.tests.SomeTestCase`) and ask it to also run the full suite afterward to check for regressions elsewhere. Wait for its pass/fail report.

4. **Write the report.** Derive a slug from the spec filename (e.g. `registration.md` → `registration`; for pasted spec text, pick a short slug from its title/goal). Write `docs/test-reports/<slug>.md` (create the `docs/test-reports/` directory if needed) containing:
   - The spec this run covers, and the date.
   - Which tests were added or found already present (from step 2), listed by class/method name.
   - Pass/fail results for both the targeted run and the full suite (from step 3).
   - For any failure: the test name, the failing assertion, actual vs. expected, and whether it looks like an app bug or a test-authoring issue.
   - Any coverage gaps `test-writer`/`test-runner` flagged.
   If a report for this slug already exists, overwrite it with the latest run rather than appending.

5. **Summarize for the user.** Report, in a few lines:
   - What tests were added (from step 2).
   - Pass/fail results (from step 3), with failure details if any.
   - If there are failures, state plainly whether they look like bugs in the application code or problems with the tests themselves (per `test-runner`'s judgment), and recommend next steps — e.g. re-invoking `test-writer` to fix a bad assumption, or fixing the app code.
   - The path to the report file written in step 4.

Keep the final summary concise — a few lines, not a transcript of both agents' output.
