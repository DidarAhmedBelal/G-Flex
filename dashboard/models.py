from django.db import models
from django.conf import settings 

class SiteMetric(models.Model):
    date = models.DateField(unique=True, help_text="Date for the recorded metrics.")
    views_count = models.PositiveIntegerField(default=0)
    visits_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['date']
        verbose_name = "Site Metric"
        verbose_name_plural = "Site Metrics"

    def __str__(self):
        return f"Metrics for {self.date}"

class Earning(models.Model):
    month = models.DateField(unique=True, help_text="First day of the month for the earnings.")
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    class Meta:
        ordering = ['month']
        verbose_name = "Earning"
        verbose_name_plural = "Earnings"

    def __str__(self):
        return f"Earnings for {self.month.strftime('%B %Y')}: ${self.amount}"

