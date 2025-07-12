from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from users.models import User


class UserSerializer(serializers.ModelSerializer):

    password = serializers.CharField(write_only=True, min_length=8)
    profile_picture = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'password',
            'is_verified',
            'profile_picture',  
        ]
        extra_kwargs = {
            'email': {'required': True},
            'username': {'required': True},
            'password': {'write_only': True},
            'is_verified': {'read_only': True},
        }
        ref_name = 'CustomUserSerializer'

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance



class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        user = authenticate(username=email, password=password)  # `username=email` is correct here
        if not user:
            raise serializers.ValidationError("Invalid email or password.")
        if not user.is_active:
            raise serializers.ValidationError("Account is inactive.")

        data['user'] = user
        return data


class LoginResponseSerializer(serializers.Serializer):

    message = serializers.CharField()
    username = serializers.CharField()
    access = serializers.CharField()
    refresh = serializers.CharField()


class OTPSerializer(serializers.Serializer):

    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email does not exist.")
        return value


class SendOTPResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    email = serializers.EmailField()

class ErrorResponseSerializer(serializers.Serializer):
    error = serializers.CharField()
    detail = serializers.CharField(required=False)

class VerifyOTPSerializer(serializers.Serializer):

    email = serializers.EmailField()
    otp = serializers.CharField(min_length=6, max_length=6)

    def validate_otp(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("OTP must be numeric.")
        return value

class VerifyOTPResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    email = serializers.EmailField()


class ChangePasswordSerializer(serializers.Serializer):

    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_new_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value


class ChangePasswordResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    full_name = serializers.CharField()



class ErrorResponseSerializer(serializers.Serializer):
    error = serializers.CharField()

    class Meta:
        ref_name = "UsersErrorResponse"


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User 
        fields = ['id', 'username', 'email']  
