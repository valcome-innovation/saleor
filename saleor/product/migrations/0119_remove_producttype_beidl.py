# Generated by Django 3.0.5 on 2020-05-13 15:53

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0118_producttype_beidl'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='producttype',
            name='beidl',
        ),
    ]
