# from rest_framework.routers import DefaultRouter
# from django.urls import path
# from users.views import ( UserList,
#     LoginView,  SignupView, MyProfileView,
#     ChangePasswordView,  SetNewPasswordView, SendVerificationOTPView, VerifyAccountOTPView, SendPasswordResetOTPView, VerifyPasswordResetOTPView
#     )
# from dashboard.views import DashboardStatsView, MonthlyUserTrendView

# router = DefaultRouter()
# router.register('users', UserList, basename='user')

# urlpatterns = [
#     path('login/', LoginView.as_view(), name='login'),
#     path('signup/', SignupView.as_view(), name='signup'),
#     path('profile/', MyProfileView.as_view(), name='my-profile'),
#     path('change-password/', ChangePasswordView.as_view(), name='change-password'),
#     path('set-new-password/', SetNewPasswordView.as_view(), name='set-new-password'),
#     path("send-verification-otp/", SendVerificationOTPView.as_view()),
#     path("verify-account/", VerifyAccountOTPView.as_view()),
#     path("send-reset-otp/", SendPasswordResetOTPView.as_view()),
#     path("verify-reset-otp/", VerifyPasswordResetOTPView.as_view()),
    
#     path('dashboard/stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
#     path('dashboard/user-trend/', MonthlyUserTrendView.as_view(), name='dashboard-user-trend'),

# ]

# urlpatterns += router.urls



from rest_framework.routers import DefaultRouter
from django.urls import path, include
from users.views import UserList, NewUsersView, ActiveUsersView, LoginView, SignupView, MyProfileView, ChangePasswordView, SetNewPasswordView, SendVerificationOTPView, VerifyAccountOTPView, SendPasswordResetOTPView, VerifyPasswordResetOTPView
from dashboard.views import DashboardStatsView, MonthlyUserTrendView
from subscription.views import SubscriptionPlanViewSet, stripe_webhook, SubscribedUsersView
from donation.views import DonationViewSet 

router = DefaultRouter()
router.register('users', UserList, basename='user')
router.register('plans', SubscriptionPlanViewSet, basename='plans')
# router.register('my-subscriptions', UserSubscriptionViewSet, basename='my-subscriptions')

router.register('donations', DonationViewSet, basename='donation')
# POST /api/subscriptions/user-subscriptions/<subscription_id>/create_payment_intent/
router.register('plans', SubscriptionPlanViewSet, basename='subscriptionplan')


urlpatterns = [
    path('new-users/', NewUsersView.as_view(), name='new-users'),
    path('active-users/', ActiveUsersView.as_view(), name='active-users'),

    path('login/', LoginView.as_view(), name='login'),
    path('signup/', SignupView.as_view(), name='signup'),
    path('profile/', MyProfileView.as_view(), name='my-profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('set-new-password/', SetNewPasswordView.as_view(), name='set-new-password'),
    path("send-verification-otp/", SendVerificationOTPView.as_view()),
    path("verify-account/", VerifyAccountOTPView.as_view()),
    path("send-reset-otp/", SendPasswordResetOTPView.as_view()),
    path("verify-reset-otp/", VerifyPasswordResetOTPView.as_view()),
  
    path('dashboard/stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
    path('dashboard/user-trend/', MonthlyUserTrendView.as_view(), name='dashboard-user-trend'),

    path('webhook/stripe/', stripe_webhook, name='stripe-webhook'),

    path('subscribed-users/', SubscribedUsersView.as_view(), name='subscribed-users'),




]

urlpatterns += router.urls