from datetime import date

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from .models import Expense

User = get_user_model()

VALID = {
    "name": "Sam Carter",
    "email": "Sam@Example.com",
    "password1": "blue-harbor-lantern-42",
    "password2": "blue-harbor-lantern-42",
}


class RegistrationTests(TestCase):
    url = reverse("register")

    def setUp(self):
        # Migration 0002 seeds demo users; only count accounts created by the test.
        self.existing = set(User.objects.values_list("pk", flat=True))

    def new_users(self):
        return User.objects.exclude(pk__in=self.existing)

    def post(self, **overrides):
        return self.client.post(self.url, {**VALID, **overrides})

    def test_page_renders_fields(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        for name, autocomplete in [
            ("name", "name"),
            ("email", "email"),
            ("password1", "new-password"),
            ("password2", "new-password"),
        ]:
            self.assertContains(response, f'name="{name}"')
            self.assertContains(response, f'autocomplete="{autocomplete}"')
        for label in ["Full name", "Email", "Password", "Confirm password"]:
            self.assertContains(response, label)

    def test_valid_registration_creates_user(self):
        self.post()
        user = self.new_users().get()
        self.assertEqual(user.first_name, "Sam Carter")
        self.assertEqual(user.last_name, "")
        self.assertEqual(user.email, "sam@example.com")
        self.assertEqual(user.username, "sam")
        self.assertTrue(user.has_usable_password())
        self.assertTrue(user.check_password(VALID["password1"]))

    def test_logs_in_and_redirects_with_welcome(self):
        response = self.client.post(self.url, VALID, follow=True)
        self.assertRedirects(response, f"{reverse('expense_list')}?user=sam")
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.new_users().get().pk)
        self.assertContains(response, "Welcome, Sam Carter! Your account is ready.")

    def test_duplicate_email_any_case_rejected(self):
        User.objects.create_user("alex", email="alex@example.com")
        response = self.post(email="Alex@Example.com")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "An account with this email already exists.")
        self.assertEqual(self.new_users().count(), 1)

    def test_password_mismatch(self):
        response = self.post(password2="something-else-99")
        self.assertContains(response, "The two passwords don&#x27;t match.")
        self.assertFalse(self.new_users().exists())

    def test_weak_passwords_rejected(self):
        for password in ["12345678", "password"]:
            with self.subTest(password=password):
                response = self.post(password1=password, password2=password)
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context["form"].errors.get("password2"))
        self.assertFalse(self.new_users().exists())

    def test_password_similar_to_email_rejected(self):
        response = self.post(
            email="sunflower.gardens@example.com", password1="sunflowergardens", password2="sunflowergardens"
        )
        self.assertIn("too similar", " ".join(response.context["form"].errors["password2"]))
        self.assertFalse(self.new_users().exists())

    def test_name_required(self):
        response = self.post(name=" ")
        self.assertEqual(response.context["form"].errors["name"], ["Please enter your name."])

    def test_username_gets_numeric_suffix(self):
        self.post(email="sam@a.com")
        Client().post(self.url, {**VALID, "email": "sam@b.com"})
        self.assertEqual(
            sorted(self.new_users().values_list("username", flat=True)), ["sam", "sam2"]
        )

    def test_invalid_submit_keeps_name_and_email_but_not_passwords(self):
        response = self.post(password2="nope-nope-nope-1")
        self.assertContains(response, 'value="Sam Carter"')
        self.assertContains(response, 'value="Sam@Example.com"')
        self.assertNotContains(response, VALID["password1"])

    def test_logged_in_user_is_redirected(self):
        user = User.objects.create_user("jo", password="x")
        self.client.force_login(user)
        response = self.client.get(self.url)
        self.assertRedirects(response, f"{reverse('expense_list')}?user=jo")

    def test_post_without_csrf_rejected(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post(self.url, VALID)
        self.assertEqual(response.status_code, 403)
        self.assertFalse(self.new_users().exists())


class LoginTests(TestCase):
    url = reverse("login")

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="sam", email="Sam@Example.com", password="blue-harbor-lantern-42", first_name="Sam Carter"
        )

    def login(self, identifier="sam", password="blue-harbor-lantern-42", **extra):
        return self.client.post(self.url, {"username": identifier, "password": password, **extra})

    def test_page_renders_fields(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="username"')
        self.assertContains(response, 'name="password"')

    def test_username_login_redirects_to_own_list(self):
        response = self.login()
        self.assertRedirects(response, f"{reverse('expense_list')}?user=sam")
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.pk)

    def test_username_and_email_are_case_insensitive(self):
        for identifier in ("SAM", "sam@example.com", "SAM@EXAMPLE.COM"):
            with self.subTest(identifier=identifier):
                self.client.logout()
                self.assertEqual(self.login(identifier).status_code, 302)
                self.assertIn("_auth_user_id", self.client.session)

    def test_wrong_password_and_unknown_user_share_one_message(self):
        for identifier, password in (("sam", "wrong-password-1"), ("nobody", "blue-harbor-lantern-42")):
            with self.subTest(identifier=identifier):
                response = self.login(identifier, password)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "Incorrect username/email or password.")
                self.assertNotIn("_auth_user_id", self.client.session)

    def test_shared_email_cannot_be_used_to_sign_in(self):
        User.objects.create_user(username="sam2", email="sam@example.com", password="blue-harbor-lantern-42")
        self.assertEqual(self.login("sam@example.com").status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(self.login("sam").status_code, 302)

    def test_demo_users_cannot_sign_in(self):
        self.assertEqual(self.login("nizam", "").status_code, 200)
        self.assertEqual(self.login("nizam", "anything-at-all-1").status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_safe_next_is_followed(self):
        response = self.login(next=reverse("expense_add"))
        self.assertRedirects(response, reverse("expense_add"))

    def test_unsafe_next_is_ignored(self):
        for bad in ("https://evil.example/", "//evil.example/"):
            with self.subTest(next=bad):
                self.client.logout()
                response = self.login(next=bad)
                self.assertRedirects(response, f"{reverse('expense_list')}?user=sam")

    def test_signed_in_visitor_is_redirected_from_login_page(self):
        self.client.force_login(self.user)
        self.assertRedirects(self.client.get(self.url), f"{reverse('expense_list')}?user=sam")

    def test_welcome_message_is_shown(self):
        response = self.client.post(
            self.url, {"username": "sam", "password": "blue-harbor-lantern-42"}, follow=True)
        self.assertContains(response, "Welcome back, Sam Carter!")


class LogoutTests(TestCase):
    url = reverse("logout")

    def setUp(self):
        self.user = User.objects.create_user(username="sam", password="blue-harbor-lantern-42")
        self.client.force_login(self.user)

    def test_get_does_not_sign_out(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)
        self.assertIn("_auth_user_id", self.client.session)

    def test_post_signs_out_and_redirects(self):
        response = self.client.post(self.url, follow=True)
        self.assertRedirects(response, reverse("login"))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertContains(response, "You have been signed out.")

    def test_post_without_csrf_token_is_rejected(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        self.assertEqual(client.post(self.url).status_code, 403)
        self.assertIn("_auth_user_id", client.session)


class NavTests(TestCase):
    def test_anonymous_nav_has_sign_in_and_create_account_only(self):
        response = self.client.get(reverse("login"))
        self.assertContains(response, reverse("register"))
        self.assertNotContains(response, "Sign out")
        self.assertNotContains(response, f'href="{reverse("expense_add")}"')

    def test_signed_in_nav_has_sign_out_only(self):
        self.client.force_login(User.objects.create_user(username="sam", password="blue-harbor-lantern-42"))
        response = self.client.get(reverse("expense_list"))
        self.assertContains(response, "Sign out")
        self.assertNotContains(response, f'href="{reverse("login")}"')

    def test_register_page_links_to_sign_in(self):
        self.assertContains(self.client.get(reverse("register")), f'href="{reverse("login")}"')


class ExpenseVisibilityTests(TestCase):
    """Regular users see only their own expenses; only admins can see everyone's."""

    @classmethod
    def setUpTestData(cls):
        pw = "blue-harbor-lantern-42"
        cls.sam = User.objects.create_user(username="sam", password=pw, first_name="Sam Carter")
        cls.jo = User.objects.create_user(username="jo", password=pw, first_name="Jo Lee")
        cls.admin = User.objects.create_user(username="boss", password=pw, first_name="Boss", is_staff=True)
        cls.root = User.objects.create_superuser(username="root", password=pw)
        Expense.objects.create(user=cls.sam, title="Sam lunch", amount="10.00", category="food", date=date(2026, 1, 1))
        Expense.objects.create(
            user=cls.jo, title="Jo taxi", amount="20.00", category="transport", date=date(2026, 1, 2)
        )

    def get(self, as_user=None, **params):
        if as_user:
            self.client.force_login(as_user)
        return self.client.get(reverse("expense_list"), params)

    def test_anonymous_is_sent_to_login(self):
        response = self.get()
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('expense_list')}")

    def test_regular_user_sees_only_own_expenses(self):
        response = self.get(self.sam)
        self.assertContains(response, "Sam lunch")
        self.assertNotContains(response, "Jo taxi")
        self.assertEqual(list(response.context["expenses"]), list(self.sam.expenses.all()))

    def test_regular_user_cannot_view_others_via_query_string(self):
        for params in ({"user": "jo"}, {"user": "boss"}, {"user": "nizam"}):
            with self.subTest(params=params):
                response = self.get(self.sam, **params)
                self.assertContains(response, "Sam lunch")
                self.assertNotContains(response, "Jo taxi")

    def test_regular_user_total_and_chart_only_count_own(self):
        response = self.get(self.sam)
        self.assertEqual(response.context["total"], 10)
        self.assertEqual([c["key"] for c in response.context["by_category"]], ["food"])

    def test_regular_user_gets_no_person_switcher(self):
        response = self.get(self.sam)
        self.assertFalse(response.context["is_admin"])
        self.assertNotContains(response, "Everyone")
        self.assertNotContains(response, "?user=jo")

    def test_staff_and_superuser_see_everyone(self):
        for admin in (self.admin, self.root):
            with self.subTest(admin=admin.username):
                response = self.get(admin)
                self.assertTrue(response.context["is_admin"])
                self.assertContains(response, "Sam lunch")
                self.assertContains(response, "Jo taxi")
                self.assertContains(response, "Everyone")

    def test_admin_can_filter_by_user(self):
        response = self.get(self.admin, user="jo")
        self.assertContains(response, "Jo taxi")
        self.assertNotContains(response, "Sam lunch")


class AddExpenseAccessTests(TestCase):
    url = reverse("expense_add")

    @classmethod
    def setUpTestData(cls):
        pw = "blue-harbor-lantern-42"
        cls.sam = User.objects.create_user(username="sam", password=pw)
        cls.jo = User.objects.create_user(username="jo", password=pw)
        cls.admin = User.objects.create_user(username="boss", password=pw, is_staff=True)

    data = {"title": "Coffee", "amount": "3.50", "category": "food", "date": "2026-02-03"}

    def test_anonymous_is_sent_to_login_and_nothing_is_saved(self):
        self.assertRedirects(self.client.get(self.url), f"{reverse('login')}?next={self.url}")
        response = self.client.post(self.url, self.data)
        self.assertRedirects(response, f"{reverse('login')}?next={self.url}")
        self.assertFalse(Expense.objects.filter(title="Coffee").exists())

    def test_regular_user_form_has_no_owner_field(self):
        self.client.force_login(self.sam)
        self.assertNotContains(self.client.get(self.url), 'name="user"')

    def test_regular_user_expense_is_always_their_own(self):
        self.client.force_login(self.sam)
        response = self.client.post(self.url, {**self.data, "user": self.jo.pk})
        self.assertRedirects(response, f"{reverse('expense_list')}?user=sam")
        self.assertEqual(Expense.objects.get(title="Coffee").user, self.sam)

    def test_admin_can_choose_the_owner(self):
        self.client.force_login(self.admin)
        self.assertContains(self.client.get(self.url), 'name="user"')
        self.client.post(self.url, {**self.data, "user": self.jo.pk})
        self.assertEqual(Expense.objects.get(title="Coffee").user, self.jo)


class ExpenseEditDeleteTests(TestCase):
    """Owners edit/delete their own expenses; admins may edit/delete anyone's; others get 404."""

    @classmethod
    def setUpTestData(cls):
        pw = "blue-harbor-lantern-42"
        cls.sam = User.objects.create_user(username="sam", password=pw, first_name="Sam Carter")
        cls.jo = User.objects.create_user(username="jo", password=pw, first_name="Jo Lee")
        cls.admin = User.objects.create_user(username="boss", password=pw, is_staff=True)
        cls.mine = Expense.objects.create(
            user=cls.sam, title="Sam lunch", amount="10.00", category="food", date=date(2026, 1, 1)
        )
        cls.theirs = Expense.objects.create(
            user=cls.jo, title="Jo taxi", amount="20.00", category="transport", date=date(2026, 1, 2)
        )

    def edit_url(self, e):
        return reverse("expense_edit", args=[e.pk])

    def delete_url(self, e):
        return reverse("expense_delete", args=[e.pk])

    data = {"title": "Sam dinner", "amount": "12.50", "category": "food", "date": "2026-01-05"}

    # --- anonymous
    def test_anonymous_is_sent_to_login_and_nothing_changes(self):
        for url in (self.edit_url(self.mine), self.delete_url(self.mine)):
            with self.subTest(url=url):
                self.assertRedirects(self.client.get(url), f"{reverse('login')}?next={url}")
                self.assertRedirects(self.client.post(url, self.data), f"{reverse('login')}?next={url}")
        self.assertEqual(Expense.objects.get(pk=self.mine.pk).title, "Sam lunch")

    # --- owner: edit
    def test_edit_form_is_prefilled_and_has_no_owner_field(self):
        self.client.force_login(self.sam)
        response = self.client.get(self.edit_url(self.mine))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="Sam lunch"')
        self.assertNotContains(response, 'name="user"')

    def test_owner_edit_updates_only_that_expense(self):
        self.client.force_login(self.sam)
        response = self.client.post(self.edit_url(self.mine), self.data, follow=True)
        self.assertRedirects(response, f"{reverse('expense_list')}?user=sam")
        self.assertContains(response, "Expense updated.")
        self.mine.refresh_from_db()
        self.theirs.refresh_from_db()
        self.assertEqual((self.mine.title, str(self.mine.amount), self.mine.user), ("Sam dinner", "12.50", self.sam))
        self.assertEqual(self.theirs.title, "Jo taxi")

    def test_invalid_edit_shows_errors_keeps_input_and_saves_nothing(self):
        self.client.force_login(self.sam)
        response = self.client.post(self.edit_url(self.mine), {**self.data, "title": "", "amount": "-"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)
        self.mine.refresh_from_db()
        self.assertEqual(self.mine.title, "Sam lunch")

    def test_owner_cannot_reassign_via_submitted_user(self):
        self.client.force_login(self.sam)
        self.client.post(self.edit_url(self.mine), {**self.data, "user": self.jo.pk})
        self.mine.refresh_from_db()
        self.assertEqual(self.mine.user, self.sam)

    # --- other users: 404 on everything
    def test_other_users_expense_is_404_for_edit_and_delete(self):
        self.client.force_login(self.sam)
        for url in (self.edit_url(self.theirs), self.delete_url(self.theirs)):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 404)
                self.assertEqual(self.client.post(url, self.data).status_code, 404)
        self.theirs.refresh_from_db()
        self.assertEqual(self.theirs.title, "Jo taxi")
        self.assertTrue(Expense.objects.filter(pk=self.theirs.pk).exists())

    def test_missing_expense_is_404(self):
        self.client.force_login(self.sam)
        self.assertEqual(self.client.get(reverse("expense_edit", args=[999999])).status_code, 404)
        self.assertEqual(self.client.get(reverse("expense_delete", args=[999999])).status_code, 404)

    # --- owner: delete
    def test_delete_get_confirms_and_deletes_nothing(self):
        self.client.force_login(self.sam)
        response = self.client.get(self.delete_url(self.mine))
        self.assertContains(response, "Sam lunch")
        self.assertTrue(Expense.objects.filter(pk=self.mine.pk).exists())

    def test_delete_post_removes_exactly_that_expense(self):
        self.client.force_login(self.sam)
        response = self.client.post(self.delete_url(self.mine), follow=True)
        self.assertRedirects(response, f"{reverse('expense_list')}?user=sam")
        self.assertContains(response, "Expense deleted.")
        self.assertFalse(Expense.objects.filter(pk=self.mine.pk).exists())
        self.assertTrue(Expense.objects.filter(pk=self.theirs.pk).exists())
        self.assertEqual(response.context["total"], 0)

    def test_delete_without_csrf_token_is_rejected(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.sam)
        self.assertEqual(client.post(self.delete_url(self.mine)).status_code, 403)
        self.assertTrue(Expense.objects.filter(pk=self.mine.pk).exists())

    # --- admin
    def test_admin_can_edit_anyones_expense_and_reassign_it(self):
        self.client.force_login(self.admin)
        self.assertContains(self.client.get(self.edit_url(self.theirs)), 'name="user"')
        response = self.client.post(self.edit_url(self.theirs), {**self.data, "user": self.sam.pk})
        self.assertRedirects(response, f"{reverse('expense_list')}?user=sam")
        self.theirs.refresh_from_db()
        self.assertEqual((self.theirs.title, self.theirs.user), ("Sam dinner", self.sam))

    def test_admin_can_delete_anyones_expense(self):
        self.client.force_login(self.admin)
        response = self.client.post(self.delete_url(self.theirs))
        self.assertRedirects(response, f"{reverse('expense_list')}?user=jo")
        self.assertFalse(Expense.objects.filter(pk=self.theirs.pk).exists())

    # --- list page links
    def test_list_shows_edit_and_delete_links_for_each_visible_row(self):
        self.client.force_login(self.sam)
        response = self.client.get(reverse("expense_list"))
        self.assertContains(response, self.edit_url(self.mine))
        self.assertContains(response, self.delete_url(self.mine))
        self.assertNotContains(response, self.edit_url(self.theirs))

    def test_admin_list_links_to_every_expense(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("expense_list"))
        for e in (self.mine, self.theirs):
            self.assertContains(response, self.edit_url(e))
            self.assertContains(response, self.delete_url(e))

    def test_add_shows_success_message(self):
        self.client.force_login(self.sam)
        response = self.client.post(reverse("expense_add"), self.data, follow=True)
        self.assertContains(response, "Expense added.")
