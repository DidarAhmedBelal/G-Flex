from rest_framework.routers import DefaultRouter
from django.urls import path
from users.views import UserList
from users.views import (
    LoginView,  SignupView, MyProfileView,
    ChangePasswordView,  SetNewPasswordView, SendVerificationOTPView, VerifyAccountOTPView, SendPasswordResetOTPView, VerifyPasswordResetOTPView
    )

router = DefaultRouter()
router.register('users', UserList, basename='user')

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('signup/', SignupView.as_view(), name='signup'),
    path('profile/', MyProfileView.as_view(), name='my-profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('set-new-password/', SetNewPasswordView.as_view(), name='set-new-password'),
    path("send-verification-otp/", SendVerificationOTPView.as_view()),
    path("verify-account/", VerifyAccountOTPView.as_view()),
    path("send-reset-otp/", SendPasswordResetOTPView.as_view()),
    path("verify-reset-otp/", VerifyPasswordResetOTPView.as_view()),

]

urlpatterns += router.urls
