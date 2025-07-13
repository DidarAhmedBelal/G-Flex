# subscription/models.py
from django.db import models
from django.conf import settings
from datetime import timedelta
from django.utils import timezone

class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.PositiveIntegerField(help_text="Duration of the subscription in days.")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class UserSubscription(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    payment_status = models.CharField(max_length=50, default='pending')
    transaction_id = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ['-start_date']
        unique_together = ('user', 'plan', 'start_date')

    def __str__(self):
        return f"{self.user.email} - {self.plan.name}"

    def save(self, *args, **kwargs):
        if not self.end_date and self.plan and self.start_date:
            self.end_date = self.start_date + timedelta(days=self.plan.duration_days)
        super().save(*args, **kwargs)

    @property
    def is_current_active(self):
        return self.is_active and self.end_date > timezone.now()





