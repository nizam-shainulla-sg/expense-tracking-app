from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from expenses.models import Expense

SAMPLE_EXPENSES = {
    "nizam": [
        ("Groceries", "86.40", "food", date(2026, 9, 3)),
        ("Electricity bill", "112.00", "bills", date(2026, 9, 5)),
        ("Metro card top-up", "30.00", "transport", date(2026, 9, 8)),
        ("Running shoes", "129.99", "shopping", date(2026, 9, 12)),
        ("Dinner with family", "64.50", "food", date(2026, 9, 18)),
        ("Internet", "45.00", "bills", date(2026, 9, 20)),
    ],
    "ameen": [
        ("Coffee beans", "18.75", "food", date(2026, 9, 2)),
        ("Taxi to airport", "42.30", "transport", date(2026, 9, 6)),
        ("Phone bill", "38.00", "bills", date(2026, 9, 10)),
        ("Headphones", "199.00", "shopping", date(2026, 9, 14)),
        ("Lunch", "15.20", "food", date(2026, 9, 17)),
        ("Gym membership", "55.00", "other", date(2026, 9, 21)),
    ],
    "arsalan": [
        ("Weekly groceries", "72.10", "food", date(2026, 9, 1)),
        ("Fuel", "60.00", "transport", date(2026, 9, 4)),
        ("Rent", "950.00", "bills", date(2026, 9, 7)),
        ("Books", "34.95", "shopping", date(2026, 9, 11)),
        ("Movie tickets", "24.00", "other", date(2026, 9, 15)),
        ("Parking", "12.00", "transport", date(2026, 9, 22)),
    ],
}


class Command(BaseCommand):
    help = "Create sample expenses for the demo users (safe to run more than once)."

    def handle(self, *args, **options):
        User = get_user_model()
        created = 0
        for username, rows in SAMPLE_EXPENSES.items():
            user, _ = User.objects.get_or_create(
                username=username, defaults={"first_name": username.capitalize()}
            )
            for title, amount, category, day in rows:
                _, was_created = Expense.objects.get_or_create(
                    user=user,
                    title=title,
                    date=day,
                    defaults={"amount": Decimal(amount), "category": category},
                )
                created += was_created
        self.stdout.write(self.style.SUCCESS(f"Created {created} sample expenses."))
