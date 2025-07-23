# subscriptions/tasks.py

from celery import shared_task
from django.utils import timezone
from .models import UserSubscription
from django.contrib.auth import get_user_model

User = get_user_model()

@shared_task
def deactivate_expired_subscriptions():
    now = timezone.now()
    expired_subscriptions = UserSubscription.objects.filter(
        end_date__lte=now,
        is_active=True
    )

    for sub in expired_subscriptions:
        sub.is_active = False
        sub.save()

        # If user has no other active subscriptions, update user
        if not UserSubscription.objects.filter(user=sub.user, is_active=True).exists():
            sub.user.is_subscribed = False
            sub.user.save()
