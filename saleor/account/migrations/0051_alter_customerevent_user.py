# Generated by Django 3.2.2 on 2021-07-01 08:45

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("account", "0051_auto_20210609_1402"),
    ]

    operations = [
        migrations.AlterField(
            model_name="customerevent",
            name="user",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="events",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
