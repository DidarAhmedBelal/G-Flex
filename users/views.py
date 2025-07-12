from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.generics import (
    CreateAPIView,
    RetrieveUpdateAPIView,
    GenericAPIView,
)
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
import random
from datetime import timedelta
from rest_framework import viewsets
from rest_framework_simplejwt.tokens import RefreshToken
from drf_yasg.utils import swagger_auto_schema
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
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
    ErrorResponseSerializer
)

User = get_user_model()


class UserList(viewsets.ModelViewSet):

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]


class SignupView(CreateAPIView):

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return Response({
            'message': 'User created successfully',
            'user': response.data
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
        responses={200: LoginResponseSerializer}
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)

        return Response({
            "message": "Login successful",
            "username": user.username,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }, status=status.HTTP_200_OK)


class SendOTPView(GenericAPIView):

    serializer_class = OTPSerializer
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=OTPSerializer,
        responses={
            200: SendOTPResponseSerializer,
            404: ErrorResponseSerializer,
            429: 'Too many OTP requests. Try again after 1 hour.',
            500: ErrorResponseSerializer,
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        try:
            user = User.objects.only(
                'id', 'email', 'otp', 'otp_created_at',
                'otp_request_count', 'otp_request_reset_time'
            ).get(email=email)

            now = timezone.now()
            # Reset OTP request count if more than 1 hour has passed since last reset time
            if not user.otp_request_reset_time or now > user.otp_request_reset_time + timedelta(hours=1):
                user.otp_request_count = 0
                user.otp_request_reset_time = now

            # Enforce OTP request limit (e.g., 5 requests per hour)
            if user.otp_request_count >= 5:
                return Response({'error': 'Too many OTP requests. Try again after 1 hour.'}, status=429)

            # Generate and save OTP
            otp = str(random.randint(100000, 999999))
            user.otp = otp
            user.otp_created_at = now
            user.otp_request_count += 1
            user.save(update_fields=['otp', 'otp_created_at', 'otp_request_count', 'otp_request_reset_time'])

            # Send OTP email
            try:
                send_mail(
                    subject='Your OTP Code',
                    message=f'Your OTP code is {otp}',
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[email],
                    fail_silently=False
                )
            except Exception as e:
                return Response({'error': 'Email sending failed', 'detail': str(e)}, status=500)

            return Response({'message': 'OTP sent successfully', 'email': email}, status=200)

        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)


class VerifyOTPView(GenericAPIView):
 
    serializer_class = VerifyOTPSerializer
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=VerifyOTPSerializer,
        responses={
            200: VerifyOTPResponseSerializer,
            400: 'Invalid OTP or email / OTP expired'
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']

        try:
            user = User.objects.only('id', 'email', 'otp', 'otp_created_at', 'is_verified').get(email=email, otp=otp)
            # Check if OTP has expired (e.g., 1 minute validity)
            if not user.otp_created_at or timezone.now() > user.otp_created_at + timedelta(minutes=1):
                return Response({'error': 'OTP has expired'}, status=400)

            user.is_verified = True
            user.otp = ''  # Clear OTP after successful verification
            user.otp_created_at = None
            user.save(update_fields=['is_verified', 'otp', 'otp_created_at'])

            return Response({'message': 'OTP Verified successfully', 'email': email}, status=200)

        except User.DoesNotExist:
            return Response({'error': 'Invalid OTP or email'}, status=400)


class ChangePasswordView(GenericAPIView):

    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=ChangePasswordSerializer,
        responses={
            200: ChangePasswordResponseSerializer,
            400: 'Old password is incorrect or new password validation errors'
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        old_password = serializer.validated_data['old_password']
        new_password = serializer.validated_data['new_password']
        user = request.user

        # Verify old password
        if not user.check_password(old_password):
            return Response({'error': 'Old password is incorrect'}, status=400)

        # Validate new password against Django's password validators
        try:
            validate_password(new_password, user=user)
        except DjangoValidationError as e:
            # Re-raise as DRF ValidationError to return appropriate error messages
            raise ValidationError({'new_password': list(e.messages)})

        user.set_password(new_password)
        user.save(update_fields=["password"])

        full_name = f"{user.first_name} {user.last_name}".strip()
        return Response({'message': 'Password changed successfully', 'full_name': full_name}, status=200)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):

    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True)

    class Meta:
        fields = ['email', 'password'] # Explicitly define fields for clarity, though not strictly necessary here

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        # Authenticate user using email and password
        user = authenticate(request=self.context.get('request'), username=email, password=password)

        if not user:
            raise serializers.ValidationError("Invalid credentials")

        # Get refresh token for the authenticated user
        refresh = self.get_token(user)

        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {  # Include basic user information in the response
                'id': user.id,
                'email': user.email,
                'username': user.username,
            }
        }


class CustomTokenObtainPairView(TokenObtainPairView):

    serializer_class = CustomTokenObtainPairSerializer


