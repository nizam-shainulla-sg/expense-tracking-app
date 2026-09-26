# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Environment

- Python 3.14 and Django 6.1 live in the virtualenv at `.django_venv/` (note the non-standard name). Call its binaries directly (`.django_venv/bin/python`) or activate it with `source .django_venv/bin/activate`.
- There is no `requirements.txt`, linter or formatter configured.
- The system `/usr/bin/python3` is Apple's stub and does not work; use the venv or `/usr/local/bin/python3`.

## Commands

```bash
.django_venv/bin/python manage.py runserver              # dev server at http://localhost:8000
.django_venv/bin/python manage.py makemigrations expenses # after changing expenses/models.py
.django_venv/bin/python manage.py migrate
.django_venv/bin/python manage.py check
.django_venv/bin/python manage.py test                   # all tests
.django_venv/bin/python manage.py test expenses.tests.SomeTestCase.test_method  # single test
.django_venv/bin/python manage.py createsuperuser        # for /admin/
.django_venv/bin/python manage.py seed_expenses          # idempotent sample data for the demo users
```

Tests live in `expenses/tests.py`. Migration `0002` seeds the demo users into the test database too, so tests must count only the users they create, not assume an empty `User` table.

## Architecture

A small expense tracker with three pages: list, add, and register. Feature specs live in `docs/specs/`. `config/` is the project package (settings, root URLconf) and `expenses/` is the only app. The database is SQLite (`db.sqlite3`).

- **Routing:** `config/urls.py` mounts `/admin/` and includes `expenses.urls` at the root. The app defines the named routes `expense_list` (`/`), `expense_add` (`/add/`) and `register` (`/register/`). Templates and redirects refer to these names, not hardcoded paths.
- **Users:** each `Expense` belongs to a Django auth `User` (`related_name="expenses"`). Migration `0002_expense_user` creates the demo users `nizam`, `ameen` and `arsalan` (with unusable passwords; there is no login) and assigns any existing expenses to `nizam`. The list page filters by `?user=<username>`, and after a save the form redirects back to that filter.
- **Data flow:** the `Expense` model (user, title, amount as a `Decimal`, category from `CATEGORY_CHOICES`, date; ordered newest first) → `ExpenseForm` (a `ModelForm` that uses a native `type="date"` input) → function-based views. `expense_list` computes the total with `aggregate(Sum)` and falls back to `0` when there are no rows. `expense_add` follows the standard GET-shows-form / POST-validates-then-redirects pattern.
- **Templates:** these live in `expenses/templates/expenses/` and are found through `APP_DIRS`. Both pages extend `base.html`, which holds the shared CSS tokens (light and dark mode, with `data-theme` overrides), the nav, and the blocks `extra_head`, `hero`, `content` and `scripts`. There are no static files; page-specific CSS and JS live inline in each template. Amounts are shown with `floatformat:"2g"`.
- **Category chart:** `expense_list` passes `by_category` (sorted by total, descending) to the template, which serializes it with `json_script`. Inline JS draws the pie as SVG with no chart library. Each category's color is fixed by the CSS classes `.cat-<key>` → `--cat-<key>`, which are shared by the chart, legend and table swatches. When adding a category to `CATEGORY_CHOICES`, also add its `--cat-*` token (light and dark) and its `.cat-*` class in `base.html`.
- **Registration:** `RegistrationForm` subclasses `BaseUserCreationForm`, stores the full name in `first_name` and the email in lowercase, and generates `username` from the part of the email before the `@` (`sam`, `sam2`, …). Email uniqueness is enforced in the form only; the database does not require it. The view logs the new user in, then redirects to `/?user=<username>` with a `messages` success banner, which `base.html` renders. There is no login or logout page yet.
- **Shared form CSS:** `.form-card`, `.grid`, `.field` and error styles live in `base.html` and are used by both `add.html` and `register.html`.
- `Expense` is registered in the admin, which is currently the only way to edit or delete records.
