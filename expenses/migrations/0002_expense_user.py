from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.db import migrations, models
import django.db.models.deletion

USERS = [("nizam", "Nizam"), ("ameen", "Ameen"), ("arsalan", "Arsalan")]


def create_users(apps, schema_editor):
    User = apps.get_model("auth", "User")
    Expense = apps.get_model("expenses", "Expense")
    for username, first_name in USERS:
        User.objects.get_or_create(
            username=username,
            defaults={"first_name": first_name, "password": make_password(None)},
        )
    # Expenses created before users existed belong to Nizam.
    Expense.objects.filter(user__isnull=True).update(user=User.objects.get(username="nizam"))


class Migration(migrations.Migration):

    dependencies = [
        ("expenses", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="expense",
            name="user",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="expenses",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RunPython(create_users, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="expense",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="expenses",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
