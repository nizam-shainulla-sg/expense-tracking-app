from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

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
        response = self.post(email="sunflower.gardens@example.com", password1="sunflowergardens", password2="sunflowergardens")
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
