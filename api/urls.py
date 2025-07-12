from rest_framework.routers import DefaultRouter
from django.urls import path
from users.views import UserList
from users.views import (
    LoginView,  SignupView, MyProfileView,
    ChangePasswordView, VerifyOTPView, SendOTPView
    )

router = DefaultRouter()
router.register('users', UserList, basename='user')

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('signup/', SignupView.as_view(), name='signup'),
    path('profile/', MyProfileView.as_view(), name='my-profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('send-otp/', SendOTPView.as_view(), name='send-otp'),
]

urlpatterns += router.urls
