
from rest_framework import serializers
from .models import SubscriptionPlan, UserSubscription

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = '__all__'


class UserSubscriptionSerializer(serializers.ModelSerializer):
    plan_name = serializers.ReadOnlyField(source='plan.name')
    user_email = serializers.ReadOnlyField(source='user.email')

    class Meta:
        model = UserSubscription
        fields = '__all__'
        read_only_fields = ('user', 'start_date', 'end_date', 'is_active', 'payment_status', 'transaction_id')
