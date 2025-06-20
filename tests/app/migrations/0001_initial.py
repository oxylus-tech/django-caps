# Generated by Django 5.1.7 on 2025-06-03 17:21

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("caps", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ConcreteOwned",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("uuid", models.UUIDField(default=uuid.uuid4, verbose_name="Id")),
                ("name", models.CharField(max_length=16)),
                (
                    "owner",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="caps.agent", verbose_name="Owner"
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="ConcreteOwnedAccess",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("uuid", models.UUIDField(db_index=True, default=uuid.uuid4, verbose_name="Id")),
                (
                    "expiration",
                    models.DateTimeField(
                        blank=True,
                        help_text="Defines an expiration date after which the access is not longer valid.",
                        null=True,
                        verbose_name="Expiration",
                    ),
                ),
                ("grants", models.JSONField(blank=True, verbose_name="Granted permissions")),
                (
                    "emitter",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="+",
                        to="caps.agent",
                        verbose_name="Emitter",
                    ),
                ),
                (
                    "origin",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="derived",
                        to="caps_test.concreteownedaccess",
                        verbose_name="Origin",
                    ),
                ),
                (
                    "receiver",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="+",
                        to="caps.agent",
                        verbose_name="Receiver",
                    ),
                ),
                (
                    "target",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="accesses",
                        to="caps_test.concreteowned",
                        verbose_name="Target",
                    ),
                ),
            ],
            options={
                "abstract": False,
                "proxy": False,
            },
        ),
    ]
