from rest_framework import serializers
from .models import SiteMetric, Earning
from django.contrib.auth import get_user_model
from django.db.models.functions import TruncMonth

User = get_user_model()

class DashboardStatsSerializer(serializers.Serializer):
    new_users = serializers.IntegerField()
    active_users = serializers.IntegerField()
    total_views = serializers.IntegerField()
    total_visits = serializers.IntegerField()
    monthly_earnings = serializers.DecimalField(max_digits=10, decimal_places=2)


class MonthlyUserCountSerializer(serializers.Serializer):
    month = serializers.CharField() # YYYY-MM format
    this_year_users = serializers.IntegerField()
    last_year_users = serializers.IntegerField()