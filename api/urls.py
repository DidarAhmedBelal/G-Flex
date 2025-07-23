
from rest_framework.routers import DefaultRouter
from django.urls import path, include

# User-related views
from users.views import (
    UserList, NewUsersView, ActiveUsersView, LoginView, SignupView, MyProfileView,
    ChangePasswordView, SetNewPasswordView, SendVerificationOTPView, VerifyAccountOTPView,
    SendPasswordResetOTPView, VerifyPasswordResetOTPView, FriendBirthdayViewSet, WishMessageViewSet
)

# Dashboard
from dashboard.views import DashboardStatsView, MonthlyUserTrendView

# Subscription
from subscription.views import (
    SubscriptionPlanViewSet, UserSubscriptionViewSet, SubscribedUsersView, UnifiedStripeWebhookView
)

# Donation
from donation.views import (
    DonationViewSet, DonationCampaignViewSet, CreateDonationCheckoutSessionView,
    UserDonationSummaryView, AdminDonationSummaryView, PublicDonationSummaryView,
    YearlyDonationGraphView, MonthlyDonationGraphView, FundCollectionView, RateDonationView
)

# Terms
from terms.views import AdminTermsViewSet, PrivacyPolicyView, TermsConditionView

# Chat
from chat.views import ConversationViewSet, websocket_test_view


# ---------------------------
# Router-registered ViewSets
# ---------------------------

router = DefaultRouter()
router.register('users', UserList, basename='user')
router.register('plans', SubscriptionPlanViewSet, basename='plan')
router.register('subscriptions', UserSubscriptionViewSet, basename='subscription')
router.register('donations', DonationViewSet, basename='donation')
router.register('campaigns', DonationCampaignViewSet, basename='campaign')
router.register('conversations', ConversationViewSet, basename='conversation')
router.register('friends', FriendBirthdayViewSet, basename='friends')
router.register('wishes', WishMessageViewSet, basename='wishes')
router.register('admin/policies', AdminTermsViewSet, basename='admin-policies')


# ---------------------------
# Explicit Path URLs
# ---------------------------
urlpatterns = [
    # --- Auth ---
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/signup/', SignupView.as_view(), name='signup'),
    path('auth/profile/', MyProfileView.as_view(), name='my-profile'),
    path('auth/change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('auth/set-new-password/', SetNewPasswordView.as_view(), name='set-new-password'),
    path('auth/send-verification-otp/', SendVerificationOTPView.as_view(), name='send-verification-otp'),
    path('auth/verify-account/', VerifyAccountOTPView.as_view(), name='verify-account'),
    path('auth/send-reset-otp/', SendPasswordResetOTPView.as_view(), name='send-reset-otp'),
    path('auth/verify-reset-otp/', VerifyPasswordResetOTPView.as_view(), name='verify-reset-otp'),

    # --- Users ---
    path('users/active/', ActiveUsersView.as_view(), name='active-users'),
    path('users/new/', NewUsersView.as_view(), name='new-users'),

    # --- Dashboard ---
    path('dashboard/stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
    path('dashboard/user-trend/', MonthlyUserTrendView.as_view(), name='dashboard-user-trend'),

    # --- Subscriptions ---
    path('subscriptions/subscribed-users/', SubscribedUsersView.as_view(), name='subscribed-users'),
    # path('subscriptions/create-checkout-session/', CreateSubscriptionCheckoutSessionView.as_view(), name='create-subscription-session'),
    # POST /plans/{plan_id}/create_checkout_session/
    # path('subscriptions/webhook/stripe/', subscription_stripe_webhook, name='subscription-stripe-webhook'),

    # --- Donations ---
    path('donation/create-checkout-session/', CreateDonationCheckoutSessionView.as_view(), name='create-donation-session'),
    path('donations/summary/', UserDonationSummaryView.as_view(), name='user-donation-summary'),
    path('donations/admin-summary/', AdminDonationSummaryView.as_view(), name='admin-donation-summary'),
    path('donations/public-summary/', PublicDonationSummaryView.as_view(), name='public-donation-summary'),
    # path('donations/webhook/stripe/', StripeWebhookView.as_view(), name='donation-stripe-webhook'),

    # --- Terms ---
    # path('policies/<str:type>/', TermsByTypeListView.as_view(), name='policy-by-type'),  # Authenticated
    # path('terms/', TermsConditionView.as_view(), name='terms-condition'),                # Public
    # path('privacy/', PrivacyPolicyView.as_view(), name='privacy-policy'),                # Public
    path('terms/', TermsConditionView.as_view(), name='terms-condition'),
    path('privacy/', PrivacyPolicyView.as_view(), name='privacy-policy'),

    # --- Donation Graphs & Fund Collection ---
    path('donations/graph/monthly/', MonthlyDonationGraphView.as_view(), name='monthly-donation-graph'),
    path('donations/graph/yearly/', YearlyDonationGraphView.as_view(), name='yearly-donation-graph'),
    path('donations/fund-collection/', FundCollectionView.as_view(), name='fund-collection'),

    # --- Chat test endpoint ---
    path('test-socket/', websocket_test_view, name='websocket-test'),

    # --- Donation Rating ---
    path('donations/rate/', RateDonationView.as_view(), name='rate-donation'),

    # --- Unified Stripe Webhook ---
    path('webhooks/stripe/', UnifiedStripeWebhookView.as_view(), name='stripe-webhook'),

    # --- All registered ViewSets ---
    path('', include(router.urls)),
]
    
