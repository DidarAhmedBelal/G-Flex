from rest_framework import serializers
from .models import Donation, TotalDonation
from django.contrib.auth import get_user_model
from django.db.models import Sum

User = get_user_model()


class DonationSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    rating = serializers.IntegerField(read_only=True)

    class Meta:
        model = Donation
        fields = [
            'id',
            'user',
            'user_email',
            'donor_name',
            'donor_email',
            'amount',
            'currency',
            'message',
            'donated_at',
            'transaction_id',
            'payment_status',
            'rating',
            'is_request',
        ]
        read_only_fields = [
            'user',
            'user_email',
            'donated_at',
            'transaction_id',
            'payment_status',
            'donor_name',
            'donor_email',
            'rating',
        ]


class CreateDonationSessionSerializer(serializers.Serializer):
    amount = serializers.CharField(help_text="Donation amount (e.g. '20.00')")
    donation_id = serializers.IntegerField(required=False, help_text="(Optional) ID of admin-created donation request")
    donor_name = serializers.CharField(required=False, help_text="Optional if user is authenticated")
    donor_email = serializers.EmailField(required=False, help_text="Required for guest users")
    message = serializers.CharField(required=False, allow_blank=True, help_text="Optional message")


class RateDonationSerializer(serializers.Serializer):
    rating = serializers.IntegerField(
        min_value=1,
        max_value=5,
        help_text="Rating from 1 to 5"
    )





class UserDonationSummarySerializer(serializers.Serializer):
    total_donated = serializers.DecimalField(max_digits=12, decimal_places=2)


class PerUserDonationSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    user_email = serializers.EmailField()
    user_total = serializers.DecimalField(max_digits=12, decimal_places=2)


class AdminDonationSummarySerializer(serializers.Serializer):
    total_all_users = serializers.DecimalField(max_digits=15, decimal_places=2)
    per_user_donations = PerUserDonationSerializer(many=True)


class TotalDonationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TotalDonation
        fields = ['total_amount', 'total_count']
