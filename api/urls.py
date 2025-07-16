from rest_framework.routers import DefaultRouter
from django.urls import path, include

from users.views import (
    UserList, NewUsersView, ActiveUsersView, LoginView, SignupView, MyProfileView,
    ChangePasswordView, SetNewPasswordView, SendVerificationOTPView, VerifyAccountOTPView,
    SendPasswordResetOTPView, VerifyPasswordResetOTPView
)
from dashboard.views import DashboardStatsView, MonthlyUserTrendView
from subscription.views import (
    SubscriptionPlanViewSet, UserSubscriptionViewSet, SubscribedUsersView, stripe_webhook as subscription_stripe_webhook
)
from terms.views import ( AdminTermsListCreateView, AdminTermsDetailView, TermsByTypeListView)   
from donation.views import ( CreateDonationCheckoutSessionView, StripeWebhookView, DonationViewSet)
from chat.views import ConversationViewSet, websocket_test_view
router = DefaultRouter()
router.register('users', UserList, basename='user')
router.register('plans', SubscriptionPlanViewSet, basename='plan')
router.register('subscriptions', UserSubscriptionViewSet, basename='subscription')
router.register('donations', DonationViewSet, basename='donation')
router.register('conversations', ConversationViewSet, basename='conversation')
# POST /api/conversations/1/send_message/


# POST message:
# POST /api/conversations/<conversation_id>/send_message/
# → Sends user message, stores reply.

# GET chat history:
# GET /api/conversations/<conversation_id>/messages/
# → Returns all messages (user + AI) for that conversation.

urlpatterns = [
    # User-related endpoints
    path('users/active/', ActiveUsersView.as_view(), name='active-users'),
    path('users/new/', NewUsersView.as_view(), name='new-users'),

    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/signup/', SignupView.as_view(), name='signup'),
    path('auth/profile/', MyProfileView.as_view(), name='my-profile'),
    path('auth/change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('auth/set-new-password/', SetNewPasswordView.as_view(), name='set-new-password'),

    path('auth/send-verification-otp/', SendVerificationOTPView.as_view(), name='send-verification-otp'),
    path('auth/verify-account/', VerifyAccountOTPView.as_view(), name='verify-account'),
    path('auth/send-reset-otp/', SendPasswordResetOTPView.as_view(), name='send-reset-otp'),
    path('auth/verify-reset-otp/', VerifyPasswordResetOTPView.as_view(), name='verify-reset-otp'),

    # Dashboard endpoints
    path('dashboard/stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
    path('dashboard/user-trend/', MonthlyUserTrendView.as_view(), name='dashboard-user-trend'),

    # Subscription related
    path('subscriptions/subscribed-users/', SubscribedUsersView.as_view(), name='subscribed-users'),
    path('subscriptions/webhook/stripe/', subscription_stripe_webhook, name='subscription-stripe-webhook'),

    path('donation/create-checkout-session/', CreateDonationCheckoutSessionView.as_view(), name='create-donation-session'),
    path('stripe/webhook/', StripeWebhookView.as_view(), name='stripe-webhook'),
    path('terms/', AdminTermsListCreateView.as_view(), name='admin-terms-list-create'),
    path('terms/<int:pk>/', AdminTermsDetailView.as_view(), name='admin-terms-detail'),
    
    # Public view (read-only)
    path('terms/<str:type>/', TermsByTypeListView.as_view(), name='terms-by-type'),
    path("test-socket/", websocket_test_view, name="websocket-test"),

    # Include all router-registered URLs
    path('', include(router.urls)),
]
