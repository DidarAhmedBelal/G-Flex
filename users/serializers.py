from .models import Country


from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from users.models import User, FriendBirthday, WishMessage

from subscription.models import UserSubscription  
from subscription.serializers import UserSubscriptionSerializer  

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, required=True)
    profile_picture = serializers.ImageField(required=False, allow_null=True)
    age = serializers.ReadOnlyField()
    subscriptions = UserSubscriptionSerializer(many=True, read_only=True) 

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'phone_number',
            'password',
            'is_verified',
            'profile_picture',
            'date_of_birth',
            'age',
            'is_subscribed',
            'subscriptions',  
        ]
        extra_kwargs = {
            'email': {'required': True},
            'password': {'write_only': True},
            'is_verified': {'read_only': True},
            'is_subscribed': {'read_only': True},
            'date_of_birth': {'required': False, 'allow_null': True},
        }
        ref_name = 'CustomUserSerializer'



class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ['id', 'user', 'country']
        read_only_fields = ['id', 'user']


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            raise serializers.ValidationError("Both email and password are required.")

        user = authenticate(username=email, password=password)

        if not user:
            raise serializers.ValidationError("Invalid email or password.")
        if not user.is_active:
            raise serializers.ValidationError("Account is inactive.")

        data['user'] = user
        return data

class LoginResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()

    class Meta:
        ref_name = "LoginResponse"

class OTPSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email does not exist.")
        return value


class SendOTPResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    email = serializers.EmailField()

    class Meta:
        ref_name = "SendOTPResponse"


class ErrorResponseSerializer(serializers.Serializer):
    error = serializers.CharField()
    detail = serializers.CharField(required=False, allow_null=True)

    class Meta:
        ref_name = "GenericErrorResponse"


class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    otp = serializers.CharField(min_length=6, max_length=6, required=True)

    def validate_otp(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("OTP must be numeric.")
        return value


class VerifyOTPResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    email = serializers.EmailField()

    class Meta:
        ref_name = "VerifyOTPResponse"


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, min_length=8, required=True)

    def validate_new_password(self, value):
        try:
            validate_password(value, user=self.context.get('request', {}).user)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value


class ChangePasswordResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    full_name = serializers.CharField()

    class Meta:
        ref_name = "ChangePasswordResponse"


class SetNewPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    new_password = serializers.CharField(write_only=True, min_length=8, required=True)
    confirm_password = serializers.CharField(write_only=True, min_length=8, required=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})

        try:
            validate_password(data['new_password'])
        except DjangoValidationError as e:
            raise serializers.ValidationError({'new_password': list(e.messages)})

        return data

    class Meta:
        ref_name = "SetNewPassword"


class MessageResponseSerializer(serializers.Serializer):
    message = serializers.CharField()

    class Meta:
        ref_name = "MessageResponse"




from rest_framework import serializers
from .models import FriendBirthday, WishMessage

class FriendBirthdaySerializer(serializers.ModelSerializer):
    class Meta:
        model = FriendBirthday
        fields = ['id', 'name', 'relation', 'birthday']
        read_only_fields = ['id']

class WishMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = WishMessage
        fields = ['id', 'message']
