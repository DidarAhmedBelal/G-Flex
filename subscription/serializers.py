# subscriptions/serializers.py

from rest_framework import serializers
from .models import SubscriptionPlan, UserSubscription, SubscriptionFeature

# Feature serializer
class SubscriptionFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionFeature
        fields = ['description']

# Plan serializer with nested features
class SubscriptionPlanSerializer(serializers.ModelSerializer):
    duration_weeks = serializers.SerializerMethodField(read_only=True)
    features = SubscriptionFeatureSerializer(many=True)

    class Meta:
        model = SubscriptionPlan
        fields = [
            'id',
            'name',
            'description',
            'price',
            'duration_days',
            'duration_weeks',
            'is_active',
            'created_at',
            'updated_at',
            'features',
        ]
        read_only_fields = ['duration_weeks', 'created_at', 'updated_at']

    def get_duration_weeks(self, obj):
        return obj.duration_days // 7

    def create(self, validated_data):
        features_data = validated_data.pop('features', [])
        plan = SubscriptionPlan.objects.create(**validated_data)
        for feature in features_data:
            SubscriptionFeature.objects.create(plan=plan, **feature)
        return plan

    def update(self, instance, validated_data):
        features_data = validated_data.pop('features', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if features_data is not None:
            instance.features.all().delete()
            for feature in features_data:
                SubscriptionFeature.objects.create(plan=instance, **feature)

        return instance

# Plan summary serializer (for embedding inside subscription)
class SubscriptionPlanSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = ['id', 'name', 'price', 'duration_days', 'is_active']

# Final cleaned-up UserSubscriptionSerializer
class UserSubscriptionSerializer(serializers.ModelSerializer):
    plan = SubscriptionPlanSummarySerializer()  # nested plan info

    class Meta:
        model = UserSubscription
        fields = ['id', 'plan', 'start_date', 'end_date', 'is_active', 'payment_status']
