# Generated by Django 5.2.4 on 2025-07-14 02:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('donation', '0003_remove_donation_user_subscription'),
    ]

    operations = [
        migrations.AddField(
            model_name='donation',
            name='is_request',
            field=models.BooleanField(default=False, help_text='True if created by admin as a donation request'),
        ),
    ]
