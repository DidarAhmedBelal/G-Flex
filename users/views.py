from .models import Country
from .serializers import CountrySerializer

# Country selection endpoints
from rest_framework import mixins

from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.generics import CreateAPIView, RetrieveUpdateAPIView, GenericAPIView
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
import random
from datetime import timedelta
from rest_framework_simplejwt.tokens import RefreshToken
from drf_yasg.utils import swagger_auto_schema
from rest_framework.generics import ListAPIView
from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from datetime import date, timedelta
from .models import FriendBirthday, WishMessage
from .serializers import FriendBirthdaySerializer, WishMessageSerializer
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from datetime import date, timedelta
from .models import FriendBirthday, WishMessage
from .serializers import FriendBirthdaySerializer, WishMessageSerializer
from .serializers import (
    UserSerializer,
    LoginSerializer,
    LoginResponseSerializer,
    OTPSerializer,
    VerifyOTPSerializer,
    ChangePasswordSerializer,
    VerifyOTPResponseSerializer,
    ChangePasswordResponseSerializer,
    SendOTPResponseSerializer,
    ErrorResponseSerializer,
    SetNewPasswordSerializer,
    MessageResponseSerializer
)

User = get_user_model()

class UserList(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]

class NewUsersView(ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser] 
    def get_queryset(self):
        one_week_ago = timezone.now() - timedelta(days=7)
        return User.objects.filter(date_joined__gte=one_week_ago).order_by('-date_joined')

class ActiveUsersView(ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
    def get_queryset(self):
        return User.objects.filter(is_verified=True).order_by('-last_login')
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'count': queryset.count(),
            'results': serializer.data
        })



class CountryViewSet(viewsets.ModelViewSet):
    serializer_class = CountrySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Country.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class SignupView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({
            'message': 'User created successfully',
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)


class MyProfileView(RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    def get_object(self):
        return self.request.user


class LoginView(APIView):
    permission_classes = [AllowAny]
    @swagger_auto_schema(
        request_body=LoginSerializer,
        responses={
            200: LoginResponseSerializer,  
            400: ErrorResponseSerializer
        }
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        user_data = UserSerializer(user).data  
        return Response({
            "message": "Login successful",
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": user_data  
        }, status=status.HTTP_200_OK)




class SendVerificationOTPView(GenericAPIView):
    serializer_class = OTPSerializer
    permission_classes = [AllowAny]
    @swagger_auto_schema(
        request_body=OTPSerializer,
        responses={
            200: SendOTPResponseSerializer,
            404: ErrorResponseSerializer,
            429: ErrorResponseSerializer,
            500: ErrorResponseSerializer,
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
            if user.is_verified:
                return Response({'error': 'User already verified.'}, status=400)
            now = timezone.now()
            if not user.otp_request_reset_time or now > user.otp_request_reset_time + timedelta(hours=1):
                user.otp_request_count = 0
                user.otp_request_reset_time = now

            if user.otp_request_count >= 5:
                return Response({'error': 'Too many OTP requests.', 'detail': 'Try again after 1 hour.'},
                                status=status.HTTP_429_TOO_MANY_REQUESTS)
            otp = str(random.randint(100000, 999999))
            user.otp = otp
            user.otp_created_at = now
            user.otp_request_count += 1
            user.save(update_fields=['otp', 'otp_created_at', 'otp_request_count', 'otp_request_reset_time'])
            send_mail(
                subject='Verify Your Account',
                message=f'Your OTP to verify your account is {otp}',
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[email],
                fail_silently=False
            )
            return Response({'message': 'Verification OTP sent successfully', 'email': email}, status=200)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)



class VerifyAccountOTPView(GenericAPIView):
    serializer_class = VerifyOTPSerializer
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=VerifyOTPSerializer,
        responses={
            200: VerifyOTPResponseSerializer,
            400: ErrorResponseSerializer,
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']
        try:
            user = User.objects.get(email=email, otp=otp)

            if not user.otp_created_at or timezone.now() > user.otp_created_at + timedelta(minutes=1):
                return Response({'error': 'OTP has expired'}, status=400)
            user.otp = ''
            user.otp_created_at = None
            user.is_verified = True
            user.save(update_fields=['otp', 'otp_created_at', 'is_verified'])
            return Response({'message': 'Account verified successfully', 'email': email}, status=200)
        except User.DoesNotExist:
            return Response({'error': 'Invalid OTP or email'}, status=400)




class SendPasswordResetOTPView(GenericAPIView):
    serializer_class = OTPSerializer
    permission_classes = [AllowAny]
    @swagger_auto_schema(
        request_body=OTPSerializer,
        responses={
            200: SendOTPResponseSerializer,
            404: ErrorResponseSerializer,
            400: ErrorResponseSerializer,
            429: ErrorResponseSerializer,
            500: ErrorResponseSerializer,
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
            if not user.is_verified:
                return Response({'error': 'User is not verified. Cannot send reset OTP.'}, status=400)
            now = timezone.now()
            if not user.otp_request_reset_time or now > user.otp_request_reset_time + timedelta(hours=1):
                user.otp_request_count = 0
                user.otp_request_reset_time = now
            if user.otp_request_count >= 5:
                return Response({'error': 'Too many OTP requests.', 'detail': 'Try again after 1 hour.'},
                                status=status.HTTP_429_TOO_MANY_REQUESTS)
            otp = str(random.randint(100000, 999999))
            user.otp = otp
            user.otp_created_at = now
            user.otp_request_count += 1
            user.reset_password = False  
            user.save(update_fields=['otp', 'otp_created_at', 'otp_request_count', 'otp_request_reset_time', 'reset_password'])
            send_mail(
                subject='Reset Your Password',
                message=f'Your OTP to reset your password is {otp}',
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[email],
                fail_silently=False
            )
            return Response({'message': 'Password reset OTP sent successfully', 'email': email}, status=200)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)




class VerifyPasswordResetOTPView(GenericAPIView):
    serializer_class = VerifyOTPSerializer
    permission_classes = [AllowAny]
    @swagger_auto_schema(
        request_body=VerifyOTPSerializer,
        responses={
            200: VerifyOTPResponseSerializer,
            400: ErrorResponseSerializer,
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']
        try:
            user = User.objects.get(email=email, otp=otp)
            if not user.is_verified:
                return Response({'error': 'User is not verified'}, status=400)

            if not user.otp_created_at or timezone.now() > user.otp_created_at + timedelta(minutes=1):
                return Response({'error': 'OTP has expired'}, status=400)
            user.otp = ''
            user.otp_created_at = None
            user.reset_password = True
            user.save(update_fields=['otp', 'otp_created_at', 'reset_password'])
            return Response({'message': 'OTP verified. You can now reset your password.', 'email': email}, status=200)
        except User.DoesNotExist:
            return Response({'error': 'Invalid OTP or email'}, status=400)




class ChangePasswordView(GenericAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        request_body=ChangePasswordSerializer,
        responses={
            200: ChangePasswordResponseSerializer,
            400: ErrorResponseSerializer 
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request}) 
        serializer.is_valid(raise_exception=True)
        old_password = serializer.validated_data['old_password']
        new_password = serializer.validated_data['new_password']
        user = request.user

        if not user.check_password(old_password):
            return Response(
                {'error': 'Old password is incorrect', 'detail': 'The old password you provided does not match your current password.'},
                status=status.HTTP_400_BAD_REQUEST
            )
 
        user.set_password(new_password)
        user.save(update_fields=["password"])
        full_name = f"{user.first_name} {user.last_name}".strip()
        return Response(
            {'message': 'Password changed successfully', 'full_name': full_name},
            status=status.HTTP_200_OK
        )




class SetNewPasswordView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = SetNewPasswordSerializer
    @swagger_auto_schema(
        request_body=SetNewPasswordSerializer,
        responses={
            200: MessageResponseSerializer,      
            400: ErrorResponseSerializer,
            403: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        new_password = serializer.validated_data['new_password']
        try:
            user = User.objects.get(email=email)

            if not user.reset_password:
                return Response(
                    {'error': 'Forbidden', 'detail': 'OTP verification required before resetting password.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            user.set_password(new_password)
            user.reset_password = False
            user.save(update_fields=['password', 'reset_password'])
            return Response(
                {'message': 'Password reset successful.'},
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found', 'detail': 'No user registered with this email address.'},
                status=status.HTTP_404_NOT_FOUND
            )

from datetime import date, timedelta
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import FriendBirthday, WishMessage
from .serializers import FriendBirthdaySerializer, WishMessageSerializer


class FriendBirthdayViewSet(viewsets.ModelViewSet):
    serializer_class = FriendBirthdaySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Prevent schema generation errors in Swagger
        if getattr(self, 'swagger_fake_view', False):
            return FriendBirthday.objects.none()

        # Protect from AnonymousUser
        if not self.request.user.is_authenticated:
            return FriendBirthday.objects.none()

        return FriendBirthday.objects.filter(user=self.request.user).order_by('birthday')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get friends whose birthday is today."""
        today = date.today()
        friends = self.get_queryset().filter(
            birthday__month=today.month,
            birthday__day=today.day
        )
        serializer = self.get_serializer(friends, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get friends with upcoming birthdays in the next 30 days."""
        today = date.today()
        upcoming_date = today + timedelta(days=30)
        friends = self.get_queryset().filter(
            birthday__gt=today,
            birthday__lte=upcoming_date
        )
        serializer = self.get_serializer(friends, many=True)
        return Response(serializer.data)


class WishMessageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = WishMessage.objects.all()
    serializer_class = WishMessageSerializer
    permission_classes = [permissions.AllowAny]
