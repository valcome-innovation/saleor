# Generated by Django 3.2.12 on 2023-03-20 15:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0056_merge_20210903_0640'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='newsletter_status',
            field=models.CharField(choices=[('subscribed', 'subscribed'), ('unsubscribed', 'unsubscribed'), ('cleaned', 'cleaned'), ('pending', 'pending'), ('transactional', 'transactional')], default='pending', max_length=35),
        ),
    ]
