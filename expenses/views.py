from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.db.models import Count, Sum
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import ExpenseForm, RegistrationForm
from .models import Expense


def expense_list(request):
    users = get_user_model().objects.order_by("first_name")
    selected_user = users.filter(username=request.GET.get("user")).first()

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
        },
    )


def expense_add(request):
    if request.method == "POST":
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save()
            return redirect(f"{reverse('expense_list')}?user={expense.user.username}")
    else:
        initial = {"date": timezone.localdate()}
        user = get_user_model().objects.filter(username=request.GET.get("user")).first()
        if user:
            initial["user"] = user
        form = ExpenseForm(initial=initial)
    return render(request, "expenses/add.html", {"form": form})


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
