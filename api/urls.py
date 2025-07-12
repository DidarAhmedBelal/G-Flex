from django.urls import path
from rest_framework.routers import DefaultRouter
from users.views import (
    UserList,
    SignupView,
    MyProfileView,
    LoginView,
    ChangePasswordView,
    VerifyOTPView,
    SendOTPView,
    )

urlpatterns = [
    
path('login/', LoginView.as_view(), name='login'),
path('signup/', SignupView.as_view(), name='signup'),
path('profile/', MyProfileView.as_view(), name='my-profile'),
path('change-password/', ChangePasswordView.as_view(), name='change-password'),
path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
path('send-otp/', SendOTPView.as_view(), name='send-otp'),
path('users/', UserList.as_view({'get': 'list', 'post': 'create'}), name='user-list'),

]