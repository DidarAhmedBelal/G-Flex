from rest_framework import serializers
from .models import Donation, TotalDonation, DonationCampaign
from django.contrib.auth import get_user_model

User = get_user_model()


# ----------------------------
# Campaign Serializers
# ----------------------------

class DonationCampaignSerializer(serializers.ModelSerializer):
    progress_percentage = serializers.SerializerMethodField()
    raised_display = serializers.SerializerMethodField()
    class Meta:
        model = DonationCampaign
        fields = [
            'id',
            'title',
            'organization',
            'description',
            'goal_amount',
            'raised_amount',
            'supporters',
            'thumbnail',
            'is_active',
            'created_at',
            'progress_percentage',
            'raised_display',
        ]

    def get_progress_percentage(self, obj):
        return obj.progress_percentage()
    
    def get_raised_display(self, obj):
        percentage = obj.progress_percentage()
        return f"${obj.raised_amount} ({percentage}%)"


class CreateDonationCampaignSerializer(serializers.ModelSerializer):
    class Meta:
        model = DonationCampaign
        fields = [
            'title',
            'organization',
            'description',
            'goal_amount',
            'thumbnail',
            'is_active',
        ]


# ----------------------------
# Donation Serializers
# ----------------------------

class DonationSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    campaign_title = serializers.CharField(source='campaign.title', read_only=True)

    class Meta:
        model = Donation
        fields = [
            'id',
            'user',
            'user_email',
            'campaign',
            'campaign_title',
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
            'rating',
            'donor_name',
            'donor_email',
        ]


class CreateDonationSessionSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    campaign_id = serializers.IntegerField(required=True)
    donation_id = serializers.IntegerField(required=False, help_text="(Optional) ID of admin-created donation request")
    donor_name = serializers.CharField(required=False, allow_blank=True)
    donor_email = serializers.EmailField(required=False)
    message = serializers.CharField(required=False, allow_blank=True)


class RateDonationSerializer(serializers.Serializer):
    rating = serializers.IntegerField(min_value=1, max_value=5)


# ----------------------------
# Summary & Stats Serializers
# ----------------------------

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


class RateDonationInputSerializer(serializers.Serializer):
    donation_id = serializers.IntegerField()
    rating = serializers.IntegerField(min_value=1, max_value=5)
