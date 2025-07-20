from django.db import models
from django.conf import settings
import uuid


class Donation(models.Model):
    PAYMENT_STATUSES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='donations'
    )
    donor_name = models.CharField(max_length=255, blank=True, null=True)
    donor_email = models.EmailField(blank=True, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    message = models.TextField(blank=True)
    donated_at = models.DateTimeField(auto_now_add=True)

    # Temporarily allow null=True to prevent migration crash
    transaction_id = models.CharField(max_length=255, unique=True, blank=True, null=True)

    payment_status = models.CharField(
        max_length=50,
        choices=PAYMENT_STATUSES,
        default='pending'
    )
    rating = models.PositiveSmallIntegerField(null=True, blank=True, help_text="1-5 star rating")
    is_request = models.BooleanField(default=False, help_text="True if created by admin as a donation request")

    class Meta:
        ordering = ['-donated_at']

    def __str__(self):
        return f"Donation of ${self.amount} by {self.donor_name or (self.user.email if self.user else 'Guest')}"


class TotalDonation(models.Model):
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    total_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Total Donations: ${self.total_amount} from {self.total_count} donations"

    @classmethod
    def update_totals(cls, amount):
        total_donation, created = cls.objects.get_or_create(id=1)
        total_donation.total_amount += amount
        total_donation.total_count += 1
        total_donation.save()
