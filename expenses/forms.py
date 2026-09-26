import re

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import BaseUserCreationForm

from .models import Expense


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ["user", "title", "amount", "category", "date"]
        labels = {"user": "Who spent it?"}
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "e.g. Groceries"}),
            "amount": forms.NumberInput(attrs={"placeholder": "0.00", "step": "0.01", "min": "0"}),
            "date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["user"].queryset = self.fields["user"].queryset.order_by("first_name")
        self.fields["user"].label_from_instance = lambda u: u.get_full_name() or u.username


def generate_username(email):
    """Build a unique username from the email's local part, e.g. sam, sam2."""
    User = get_user_model()
    base = re.sub(r"[^a-z0-9._-]", "", email.split("@")[0].lower())[:30] or "user"
    username, n = base, 1
    while User.objects.filter(username__iexact=username).exists():
        n += 1
        username = f"{base}{n}"
    return username


class RegistrationForm(BaseUserCreationForm):
    error_messages = {"password_mismatch": "The two passwords don't match."}

    name = forms.CharField(
        label="Full name",
        min_length=2,
        max_length=150,
        error_messages={
            "required": "Please enter your name.",
            "min_length": "Please enter your name.",
        },
        widget=forms.TextInput(attrs={"autocomplete": "name", "placeholder": "e.g. Sam Carter", "autofocus": True}),
    )

    class Meta:
        model = get_user_model()
        fields = ["email"]
        widgets = {
            "email": forms.EmailInput(attrs={"autocomplete": "email", "placeholder": "you@example.com"}),
        }

    field_order = ["name", "email", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        email = self.fields["email"]
        email.required = True
        email.label = "Email"
        email.error_messages["required"] = "Enter a valid email address."
        self.fields["password1"].label = "Password"
        self.fields["password2"].label = "Confirm password"
        self.fields["password2"].help_text = ""
        for name in ("password1", "password2"):
            self.fields[name].widget.attrs["autocomplete"] = "new-password"

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if get_user_model().objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def _post_clean(self):
        # Set the name before the password validators run, so
        # UserAttributeSimilarityValidator can compare against it.
        self.instance.first_name = self.cleaned_data.get("name", "")
        super()._post_clean()

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["name"]
        user.username = generate_username(user.email)
        if commit:
            user.save()
        return user
