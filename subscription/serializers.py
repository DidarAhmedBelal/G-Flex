from rest_framework import serializers
from .models import SubscriptionPlan
from rest_framework import serializers
from .models import UserSubscription
from donation.models import Donation

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    duration_weeks = serializers.SerializerMethodField()

    class Meta:
        model = SubscriptionPlan
        fields = '__all__'

    def get_duration_weeks(self, obj):
        return obj.duration_days // 7



class UserSubscriptionSerializer(serializers.ModelSerializer):
    plan_name = serializers.ReadOnlyField(source='plan.name')
    user_email = serializers.ReadOnlyField(source='user.email')
    donations = serializers.StringRelatedField(many=True)


    class Meta:
        model = UserSubscription
        fields = '__all__'
        read_only_fields = (
            'user',
            'start_date',
            'end_date',
            'is_active',
            'payment_status',
            'transaction_id',
            'plan_name',
            'user_email',
        )
