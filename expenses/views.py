from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .auth import LoginForm
from .forms import ExpenseForm, RegistrationForm
from .models import Expense


def is_admin(user):
    """Admins (staff or superusers) may see and choose any user's expenses."""
    return user.is_staff or user.is_superuser


@login_required
def expense_list(request):
    admin = is_admin(request.user)
    if admin:
        users = get_user_model().objects.order_by("first_name")
        selected_user = users.filter(username=request.GET.get("user")).first()
    else:
        # Everyone else only ever sees their own expenses; ?user= is ignored.
        users = get_user_model().objects.none()
        selected_user = request.user

    expenses = Expense.objects.select_related("user")
    if selected_user:
        expenses = expenses.filter(user=selected_user)

    total = expenses.aggregate(total=Sum("amount"))["total"] or 0
    labels = dict(Expense.CATEGORY_CHOICES)
    by_category = [
        {
            "key": row["category"],
            "label": labels.get(row["category"], row["category"]),
            "total": float(row["total"]),
            "count": row["count"],
        }
        for row in expenses.values("category")
        .annotate(total=Sum("amount"), count=Count("id"))
        .order_by("-total")
    ]

    return render(
        request,
        "expenses/list.html",
        {
            "expenses": expenses,
            "total": total,
            "count": len(expenses),
            "top_category": by_category[0] if by_category else None,
            "by_category": by_category,
            "users": users,
            "selected_user": selected_user,
            "is_admin": admin,
        },
    )


@login_required
def expense_add(request):
    admin = is_admin(request.user)
    if request.method == "POST":
        form = ExpenseForm(request.POST, choose_user=admin)
        if form.is_valid():
            expense = form.save(commit=False)
            if not admin:
                expense.user = request.user  # never trust a submitted owner
            expense.save()
            messages.success(request, "Expense added.")
            return redirect(f"{reverse('expense_list')}?user={expense.user.username}")
    else:
        initial = {"date": timezone.localdate()}
        if admin:
            user = get_user_model().objects.filter(username=request.GET.get("user")).first()
            if user:
                initial["user"] = user
        form = ExpenseForm(initial=initial, choose_user=admin)
    return render(request, "expenses/add.html", {"form": form})


def own_or_any_expense(request, pk):
    """Admins may reach any expense; everyone else only their own (anyone else's is a 404)."""
    if is_admin(request.user):
        return get_object_or_404(Expense, pk=pk)
    return get_object_or_404(Expense, pk=pk, user=request.user)


@login_required
def expense_edit(request, pk):
    expense = own_or_any_expense(request, pk)
    admin = is_admin(request.user)
    if request.method == "POST":
        form = ExpenseForm(request.POST, instance=expense, choose_user=admin)
        if form.is_valid():
            expense = form.save()
            messages.success(request, "Expense updated.")
            return redirect(f"{reverse('expense_list')}?user={expense.user.username}")
    else:
        form = ExpenseForm(instance=expense, choose_user=admin)
    return render(request, "expenses/add.html", {
        "form": form,
        "title": "Edit expense",
        "heading": "Edit an expense",
        "intro": "Change the details below and save.",
        "submit_label": "Save changes",
    })


@login_required
def expense_delete(request, pk):
    expense = own_or_any_expense(request, pk)
    if request.method == "POST":
        owner = expense.user.username
        expense.delete()
        messages.success(request, "Expense deleted.")
        return redirect(f"{reverse('expense_list')}?user={owner}")
    return render(request, "expenses/delete.html", {"expense": expense})


def register(request):
    if request.user.is_authenticated:
        return redirect(f"{reverse('expense_list')}?user={request.user.username}")
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome, {user.first_name}! Your account is ready.")
            return redirect(f"{reverse('expense_list')}?user={user.username}")
    else:
        form = RegistrationForm()
    return render(request, "expenses/register.html", {"form": form})


class SignInView(LoginView):
    template_name = "expenses/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def get_success_url(self):
        # Honors a safe ?next=, otherwise the user's own list.
        return self.get_redirect_url() or f"{reverse('expense_list')}?user={self.request.user.username}"

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Welcome back, {form.get_user().first_name or form.get_user().username}!")
        return response


@require_POST
def sign_out(request):
    logout(request)
    messages.success(request, "You have been signed out.")
    return redirect("login")
