# Generated by Django 3.0.6 on 2020-07-09 11:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("checkout", "0026_checkout_webhook_processing"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="checkout",
            options={
                "ordering": ("-last_change", "pk"),
                "permissions": (("manage_checkouts", "Manage checkouts"),),
            },
        ),
    ]
