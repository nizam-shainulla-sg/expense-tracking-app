# Spendwise — Expense Tracker

A small Django app for tracking personal expenses: a list page with a category breakdown chart, an add-expense form, and self-service registration. Built with Python 3.14 and Django 6.1, backed by SQLite.

This README is written for someone opening the repo for the first time. If you just want the quick reference, see [`CLAUDE.md`](CLAUDE.md).

## 1. Prerequisites

- The project virtualenv, `.django_venv/`, is already checked into this repo layout expectation — if it's missing, create it (`python3 -m venv .django_venv`) before continuing.
- Do **not** use the system `/usr/bin/python3` on macOS — it's Apple's stub and won't work. Use the venv's Python.

## 2. First-time setup

```bash
# 1. Create/activate the virtualenv (skip creation if .django_venv/ already exists)
python3 -m venv .django_venv
source .django_venv/bin/activate      # or call .django_venv/bin/python directly without activating

# 2. Install dependencies
pip install -r requirements.txt

# 3. Apply migrations (this also seeds three demo users: nizam, ameen, arsalan)
python manage.py migrate

# 4. Load sample expenses for those demo users (safe to re-run)
python manage.py seed_expenses

# 5. Start the dev server
python manage.py runserver
```

Open **http://localhost:8000/** — you should see the expense list for `nizam` with a category pie chart, seeded sample data, and a total.

If you didn't activate the virtualenv, prefix every command above with `.django_venv/bin/` instead (e.g. `.django_venv/bin/python manage.py migrate`).

### Optional: admin access

There's no login page yet (see §5), so the only way to edit or delete individual expenses today is through Django admin:

```bash
python manage.py createsuperuser
```

Then visit **http://localhost:8000/admin/**.

## 3. End-to-end flow: using the app

1. **List page** (`/`) — shows expenses for one user at a time via `?user=<username>` (e.g. `/?user=nizam`, `/?user=ameen`, `/?user=arsalan`), with a total and a pie chart broken down by category.
2. **Add an expense** (`/add/`) — fill in title, amount, category, and date. On save, you're redirected back to the list, filtered to whichever user you were viewing.
3. **Register** (`/register/`) — create a new account (name, email, password). This logs you in immediately and redirects you to your own filtered list at `/?user=<generated-username>`. Your username is auto-generated from your email (e.g. `sam@example.com` → `sam`, and `sam2` if that's taken) — there's no username field to fill in.

There is currently no login/logout page — registration is the only way "in," and once you close the browser there's no way to return to that identity except by admin lookup. This is intentional for now (see `docs/specs/registration.md`, §2 "Out of scope").

## 4. Running tests

```bash
python manage.py test                 # full suite
python manage.py test expenses.tests.RegistrationTests   # one class
python manage.py test expenses.tests.RegistrationTests.test_valid_registration_creates_user  # one method
```

Migration `0002` seeds the demo users into the *test* database too, so tests must count only the users/expenses they themselves create — never assume the `User` table starts empty.

## 5. The spec → test workflow (for contributors)

This repo has a lightweight process for turning a written feature spec into test coverage, using two purpose-built Claude Code subagents and a slash command that chains them:

```
docs/specs/<feature>.md          (you write this)
        │
        ▼
   /spec-test docs/specs/<feature>.md
        │
        ├─▶ test-writer   — reads the spec + real code, adds tests to expenses/tests.py
        │                    (never runs them)
        │
        ├─▶ test-runner    — runs the new tests + the full suite, reports pass/fail
        │                    (never edits test code)
        │
        ▼
docs/test-reports/<feature>.md   (written automatically)
```

**To use it:**

1. Write or update a spec under `docs/specs/` (see `docs/specs/registration.md` for the expected shape: goal, scope, behavior, acceptance criteria).
2. In Claude Code, run:
   ```
   /spec-test docs/specs/<feature>.md
   ```
3. Claude Code dispatches `test-writer` to add the tests, then `test-runner` to execute them, and writes a summary report to `docs/test-reports/<feature>.md`.

The two agents are defined in `.claude/agents/test-writer.md` and `.claude/agents/test-runner.md`, and the command in `.claude/commands/spec-test.md` — edit those files directly if you want to change the workflow (e.g. what conventions `test-writer` should follow, or how `test-runner` reports results).

You don't need the slash command to write or run tests manually — it's a convenience for keeping the "write" and "run" steps separate and getting a persisted report for free.

## 6. Project layout

```
config/                      Django project package: settings, root URLconf
expenses/                    the only app
├── models.py                Expense model
├── forms.py                 ExpenseForm, RegistrationForm
├── views.py                 expense_list, expense_add, register
├── urls.py                  named routes: expense_list, expense_add, register
├── templates/expenses/      base.html + list/add/register pages
├── management/commands/     seed_expenses
└── tests.py                 all tests live here
docs/
├── specs/                   feature specs (input to /spec-test)
└── test-reports/            generated test-run reports (output of /spec-test)
.claude/
├── agents/                  test-writer, test-runner subagent definitions
└── commands/                spec-test.md slash command
```

## 7. Common commands reference

```bash
.django_venv/bin/python manage.py runserver              # dev server at http://localhost:8000
.django_venv/bin/python manage.py makemigrations expenses # after changing expenses/models.py
.django_venv/bin/python manage.py migrate
.django_venv/bin/python manage.py check
.django_venv/bin/python manage.py test                   # all tests
.django_venv/bin/python manage.py createsuperuser        # for /admin/
.django_venv/bin/python manage.py seed_expenses           # idempotent sample data for the demo users
```

For deeper architecture notes (how the category chart renders, how usernames are generated, template block structure, etc.), see [`CLAUDE.md`](CLAUDE.md).
