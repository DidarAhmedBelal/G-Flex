from django.db import models
from django.conf import settings
from django.utils import timezone


class DonationCampaign(models.Model):
    """
    Represents a donation campaign like 
    'Donate for the survival of kids in Africa'.
    """

    title = models.CharField(max_length=255)
    organization = models.CharField(max_length=255, help_text="Name of the foundation or organization")
    description = models.TextField()
    goal_amount = models.DecimalField(max_digits=12, decimal_places=2)
    raised_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    supporters = models.PositiveIntegerField(default=0)
    thumbnail = models.ImageField(upload_to='campaigns/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def progress_percentage(self):
        if self.goal_amount > 0:
            return round((self.raised_amount / self.goal_amount) * 100, 2)
        return 0.0

    def __str__(self):
        return f"{self.title} ({self.organization})"


class Donation(models.Model):
    """
    A donation entry made by a user or anonymous guest.
    """

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

    campaign = models.ForeignKey(DonationCampaign, on_delete=models.CASCADE, related_name='donations', null=True, blank=True)

    donor_name = models.CharField(max_length=255, blank=True, null=True)
    donor_email = models.EmailField(blank=True, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    message = models.TextField(blank=True)
    donated_at = models.DateTimeField(auto_now_add=True)


    transaction_id = models.CharField(max_length=255, unique=True, blank=True, null=True)
    payment_status = models.CharField(max_length=50, choices=PAYMENT_STATUSES, default='pending')
    rating = models.PositiveSmallIntegerField(null=True, blank=True, help_text="1-5 star rating")
    is_request = models.BooleanField(default=False, help_text="True if created by admin as a donation request")

    class Meta:
        ordering = ['-donated_at']

    def __str__(self):
        name = self.donor_name or (self.user.email if self.user else 'Guest')
        return f"${self.amount} by {name} for {self.campaign.title}"

    def save(self, *args, **kwargs):
        """Auto-update campaign totals and global totals on completed donation."""
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new and self.payment_status == 'completed':
            self.campaign.raised_amount += self.amount
            self.campaign.supporters += 1
            self.campaign.save()
            TotalDonation.update_totals(self.amount)


class TotalDonation(models.Model):
    """
    Keeps track of global donation stats.
    """

    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    total_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Total: ${self.total_amount} from {self.total_count} donations"

    @classmethod
    def update_totals(cls, amount):
        obj, _ = cls.objects.get_or_create(id=1)
        obj.total_amount += amount
        obj.total_count += 1
        obj.save()
