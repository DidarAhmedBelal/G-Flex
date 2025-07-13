from django.db import models
from django.conf import settings 

class Donation(models.Model):

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                             help_text="Optional: The user who made the donation. Null if guest.")
    donor_name = models.CharField(max_length=255, blank=True, null=True,
                                  help_text="Name of the donor if not a registered user or custom name.")
    donor_email = models.EmailField(blank=True, null=True,
                                    help_text="Email of the donor for receipts, if applicable.")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    message = models.TextField(blank=True, help_text="Optional message from the donor.")
    donated_at = models.DateTimeField(auto_now_add=True)
    transaction_id = models.CharField(max_length=255, unique=True, blank=True, null=True)
    payment_status = models.CharField(max_length=50, default='pending') 

    class Meta:
        ordering = ['-donated_at']
        verbose_name = "Donation"
        verbose_name_plural = "Donations"

    def __str__(self):
        return f"Donation of ${self.amount} by {self.donor_name or (self.user.email if self.user else 'Guest')}"