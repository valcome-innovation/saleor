# Generated by Django 3.2.3 on 2021-08-24 13:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('streaming', '0002_auto_20210614_0833'),
    ]

    operations = [
        migrations.AlterField(
            model_name='streamticket',
            name='league_ids',
            field=models.CharField(blank=True, max_length=2048, null=True),
        ),
        migrations.AlterField(
            model_name='streamticket',
            name='team_ids',
            field=models.CharField(blank=True, max_length=2048, null=True),
        ),
    ]
