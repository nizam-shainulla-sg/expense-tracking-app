from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.forms import AuthenticationForm


class EmailOrUsernameBackend(ModelBackend):
    """Sign in with either the generated username or the account email (any letter case).

    Email is not unique in the database, so an email shared by several accounts matches
    none of them; the person must use a username instead.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or password is None:
            return None
        User = get_user_model()
        user = User.objects.filter(username__iexact=username).first()
        if user is None:
            matches = list(User.objects.filter(email__iexact=username)[:2])
            user = matches[0] if len(matches) == 1 else None
        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None


class LoginForm(AuthenticationForm):
    error_messages = {
        "invalid_login": "Incorrect username/email or password.",
        "inactive": "This account is inactive.",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        username = self.fields["username"]
        username.label = "Username or email"
        username.max_length = 254
        username.widget.attrs.update(
            {"autocomplete": "username", "autofocus": True, "maxlength": 254,
             "placeholder": "sam or you@example.com"}
        )
        self.fields["password"].widget.attrs["autocomplete"] = "current-password"
