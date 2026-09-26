# Spec: Registration page

**Status:** Implemented · **Date:** 2026-09-27 · **App:** `expenses` (Spendwise)

## 1. Goal

Let a new person create their own account so they can record expenses under their own name. Today the only users are the three demo users (`nizam`, `ameen`, `arsalan`), which are created by migration `0002_expense_user` and have no usable password.

## 2. Scope

**In scope**
- A public registration page at `/register/`.
- Creating a Django auth `User` from the submitted form.
- Logging the new user in right after they register, then redirecting them to their expenses.
- A "Create account" link in the nav.

**Out of scope** (each needs its own follow-up spec)
- Login and logout pages. Registration logs the user in, but the app has no way to sign in again later yet.
- Restricting pages to logged-in users, or making each person see only their own expenses.
- Email verification, password reset and social login.
- Rate limiting and CAPTCHA.
- Letting the demo users claim their accounts.

## 3. Form fields

| Field | Label | Input type | Required | Rules | `autocomplete` |
|---|---|---|---|---|---|
| `name` | Full name | text | Yes | Surrounding spaces removed; 2–150 characters | `name` |
| `email` | Email | email | Yes | Valid email address; at most 254 characters; stored in lowercase; must be unique regardless of letter case | `email` |
| `password1` | Password | password | Yes | Must pass `AUTH_PASSWORD_VALIDATORS` (see §4) | `new-password` |
| `password2` | Confirm password | password | Yes | Must match `password1` | `new-password` |

Username is not a form field. It is generated automatically (see §5.2).

Both password fields have a "Show" toggle that switches the input between `password` and `text`.

## 4. Validation

Errors are checked on the server and shown under the field they belong to, matching the existing add-expense form (`novalidate` on the form, `.has-error` on the field).

| Case | Message |
|---|---|
| Name missing or shorter than 2 characters | "Please enter your name." |
| Email missing or invalid | "Enter a valid email address." |
| Email already used, in any letter case | "An account with this email already exists." |
| Passwords don't match | "The two passwords don't match." |
| Password rejected by the validators | The validator's own message(s) |

The password validators are the ones already in `config/settings.py`:
- `UserAttributeSimilarityValidator`: the password can't be too similar to the name or email.
- `MinimumLengthValidator`: at least 8 characters.
- `CommonPasswordValidator`: rejects common passwords.
- `NumericPasswordValidator`: rejects passwords made only of numbers.

When the form has errors, the name and email are kept. Neither password field is re-filled.

## 5. Behavior

### 5.1 Flow
1. **GET `/register/`** shows an empty form. If the visitor is already logged in, they are redirected to `/?user=<their username>`.
2. **POST `/register/`** submits the form.
   - **Valid:** create the user (§5.2), call `login()`, show the success message "Welcome, <name>! Your account is ready.", then redirect to `/?user=<username>`.
   - **Invalid:** show the page again with a 200 status and the errors.

### 5.2 How the user is stored
- `first_name` holds the full name, trimmed. `last_name` is left blank. This keeps `get_full_name()` working with the existing templates.
- `email` holds the lowercased email.
- `username` is generated from the part of the email before the `@`: lowercased, with anything outside `[a-z0-9._-]` removed, and cut to 30 characters. If that username is taken, `2`, `3`, … is added to the end.
  - **Why generate it:** the list page puts `?user=<username>` in the address. Using the email there would put personal data in URLs and server logs.
- The password is hashed with `set_password`, as `UserCreationForm` does.

### 5.3 Email uniqueness
Django's built-in `User.email` is not unique in the database. The form enforces uniqueness with `User.objects.filter(email__iexact=...)`.
- Two people submitting the same email at almost the same moment could both get through. That is acceptable at this app's scale.
- A real database constraint would need a custom user model, which is out of scope.

## 6. UI

- The page extends `expenses/base.html` and follows the same layout as `add.html`:
  - The hero shows the heading "Create your account" and the subtitle "Start tracking where your money goes."
  - Below it is a `.card.form-card`, at most 560px wide and aligned like the add-expense form, with every field on its own full-width row.
- The main button says "Create account". Under the form is the line "Already have an account? Sign in", which stays hidden until the login page exists.
- The nav gets a third link, "Create account" (`register`), which is hidden when the user is logged in. The active state uses the existing `request.path` check.
- On narrow screens the nav wraps below the brand. The page must work at 375px wide without horizontal scrolling, and in both light and dark mode, using the existing tokens only.
- The success message needs a small message banner in `base.html`. It should render `messages` in the existing card style.

## 7. Implementation notes

| Piece | Location |
|---|---|
| URL | `expenses/urls.py`: `path("register/", views.register, name="register")` |
| Form | `expenses/forms.py`: `RegistrationForm`, a subclass of `django.contrib.auth.forms.BaseUserCreationForm`, with `fields = ["email"]`, plus a `name` field and a `clean_email` method |
| View | `expenses/views.py`: `register`, a function-based view matching `expense_add` |
| Template | `expenses/templates/expenses/register.html` |
| Nav and messages | `expenses/templates/expenses/base.html` |

No model or migration changes are needed.

## 8. Acceptance criteria

1. GET `/register/` returns 200 and shows the four fields with the labels and `autocomplete` values from §3.
2. A valid submission creates exactly one `User` with the full name in `first_name`, a lowercased email, a generated username and a usable, hashed password.
3. After a valid submission the user is logged in and redirected to `/?user=<username>`, where the welcome message is shown.
4. Registering `Alex@Example.com` when `alex@example.com` already exists fails with the duplicate-email message, and no user is created.
5. Mismatched passwords, `12345678` and `password` are each rejected with the right message.
6. A password very similar to the email is rejected by `UserAttributeSimilarityValidator`.
7. Two sign-ups with emails `sam@a.com` and `sam@b.com` get the usernames `sam` and `sam2`.
8. A logged-in user who opens `/register/` is redirected.
9. A POST without a CSRF token is rejected with 403.
10. The page has no horizontal scroll at 375px, in either light or dark mode.

## 9. Tests (`expenses/tests.py`)

Use `django.test.TestCase` and `self.client`, with one test for each of acceptance criteria 1–9. Run them with:

```bash
.django_venv/bin/python manage.py test expenses
```

## 10. Open questions

1. **Revealing registered emails:** the duplicate-email message tells anyone whether an email has an account. That's fine for a demo, but it should become a generic message once the app is public.
2. **Terms checkbox:** do we need a "I agree to the terms" checkbox? It's left out until there are terms to agree to.
3. **Demo users:** should the demo users get real emails and passwords, or stay as sample data only?
