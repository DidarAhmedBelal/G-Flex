from rest_framework.routers import DefaultRouter
from django.urls import path
from users.views import (
    UserList, NewUsersView, ActiveUsersView, LoginView, SignupView, MyProfileView,
    ChangePasswordView, SetNewPasswordView, SendVerificationOTPView, VerifyAccountOTPView,
    SendPasswordResetOTPView, VerifyPasswordResetOTPView
)
from dashboard.views import DashboardStatsView, MonthlyUserTrendView
from subscription.views import (
    SubscriptionPlanViewSet, stripe_webhook, SubscribedUsersView
)
from donation.views import DonationViewSet, create_donation_checkout_session

# DRF Router setup
router = DefaultRouter()
router.register('users', UserList, basename='user')
router.register('plans', SubscriptionPlanViewSet, basename='plans')
router.register('donations', DonationViewSet, basename='donation')

# Main API URL patterns
urlpatterns = [
    # User Auth & Profile
    path('login/', LoginView.as_view(), name='login'),
    path('signup/', SignupView.as_view(), name='signup'),
    path('profile/', MyProfileView.as_view(), name='my-profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('set-new-password/', SetNewPasswordView.as_view(), name='set-new-password'),

    # OTP Verification
    path('send-verification-otp/', SendVerificationOTPView.as_view(), name='send-verification-otp'),
    path('verify-account/', VerifyAccountOTPView.as_view(), name='verify-account'),
    path('send-reset-otp/', SendPasswordResetOTPView.as_view(), name='send-reset-otp'),
    path('verify-reset-otp/', VerifyPasswordResetOTPView.as_view(), name='verify-reset-otp'),

    # Dashboard
    path('dashboard/stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
    path('dashboard/user-trend/', MonthlyUserTrendView.as_view(), name='dashboard-user-trend'),

    # Subscriptions
    path('subscribed-users/', SubscribedUsersView.as_view(), name='subscribed-users'),
    path('webhook/stripe/', stripe_webhook, name='stripe-webhook'),

    # Donations
    path('donations/create-checkout-session/', create_donation_checkout_session, name='donation-checkout'),
]

# Include router URLs
urlpatterns += router.urls
