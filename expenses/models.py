from django.conf import settings
from django.db import models


class Expense(models.Model):
    CATEGORY_CHOICES = [
        ("food", "Food"),
        ("transport", "Transport"),
        ("bills", "Bills"),
        ("shopping", "Shopping"),
        ("other", "Other"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="expenses"
    )
    title = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="other")
    date = models.DateField()

    class Meta:
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"{self.title} ({self.amount})"
