# Test report: registration

**Spec:** `docs/specs/registration.md` · **Date:** 2026-09-27

## Tests

`test-writer` found the required coverage already present in `expenses/tests.py` — no changes were made.

`RegistrationTests` (12 methods) covers all 9 spec acceptance criteria plus 2 extras:

1. `test_page_renders_fields`
2. `test_valid_registration_creates_user`
3. `test_logs_in_and_redirects_with_welcome`
4. `test_duplicate_email_any_case_rejected`
5. `test_password_mismatch`, `test_weak_passwords_rejected` (subTest over `"12345678"` and `"password"`)
6. `test_password_similar_to_email_rejected`
7. `test_username_gets_numeric_suffix`
8. `test_logged_in_user_is_redirected`
9. `test_post_without_csrf_rejected`
10. Extras: `test_name_required`, `test_invalid_submit_keeps_name_and_email_but_not_passwords`

(Criterion 10 in the spec — no horizontal scroll at 375px — is CSS/viewport and correctly left untested here.)

## Run results

| Command | Result |
|---|---|
| `.django_venv/bin/python manage.py test expenses.tests.RegistrationTests` | 12/12 passed |
| `.django_venv/bin/python manage.py test` (full suite) | 12/12 passed |

No failures. No regressions elsewhere in the suite.

## Notes

- `RegistrationTests` is currently the only test class in `expenses/tests.py`. There is no test coverage yet for `expense_list`, `expense_add`, or the `Expense` model.
- Demo users (`nizam`, `ameen`, `arsalan`) seeded by migration `0002` are correctly handled by these tests via count deltas, not empty-table assumptions.
