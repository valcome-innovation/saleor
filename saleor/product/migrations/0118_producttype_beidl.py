# Generated by Django 3.0.5 on 2020-05-13 15:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0117_auto_20200423_0737'),
    ]

    operations = [
        migrations.AddField(
            model_name='producttype',
            name='beidl',
            field=models.CharField(default='yeah', max_length=250),
        ),
    ]
