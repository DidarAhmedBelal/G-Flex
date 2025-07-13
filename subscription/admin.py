from django.contrib import admin

# Register your models here.
from subscription.models import SubscriptionPlan, UserSubscription

admin.site.register(SubscriptionPlan)
admin.site.register(UserSubscription)