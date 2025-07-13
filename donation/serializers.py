# donation/serializers.py
from rest_framework import serializers
from .models import Donation

class DonationSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = Donation
        fields = '__all__'
        read_only_fields = ('user', 'donated_at', 'payment_status', 'transaction_id')