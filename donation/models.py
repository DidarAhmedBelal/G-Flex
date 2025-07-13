from django.db import models
from django.conf import settings 

class Donation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    donor_name = models.CharField(max_length=255, blank=True, null=True)
    donor_email = models.EmailField(blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    message = models.TextField(blank=True)
    donated_at = models.DateTimeField(auto_now_add=True)
    transaction_id = models.CharField(max_length=255, unique=True, blank=True, null=True)
    payment_status = models.CharField(max_length=50, default='pending') 
    rating = models.PositiveSmallIntegerField(null=True, blank=True, help_text="1-5 star rating")

    class Meta:
        ordering = ['-donated_at']

    def __str__(self):
        return f"Donation of ${self.amount} by {self.donor_name or (self.user.email if self.user else 'Guest')}"
