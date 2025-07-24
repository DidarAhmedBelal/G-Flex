from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from datetime import date
from django.utils import timezone


def user_profile_upload_path(instance, filename):
    return f"profile_pics/user_{instance.id}/{filename}"


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if not password:
            raise ValueError("Superusers must have a password.")
        if extra_fields.get('is_staff') is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get('is_superuser') is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None  # Disable default username field
    email = models.EmailField(unique=True)

    first_name = models.CharField(max_length=10, blank=True, null=True)
    last_name = models.CharField(max_length=10, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)

    profile_picture = models.ImageField(upload_to=user_profile_upload_path, blank=True, null=True)
    is_verified = models.BooleanField(default=False)

    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)
    otp_request_count = models.IntegerField(default=0)
    otp_request_reset_time = models.DateTimeField(blank=True, null=True)
    reset_password = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    is_subscribed = models.BooleanField(default=False)
    

    date_of_birth = models.DateField(blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email

    @property
    def age(self):
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None


class FriendBirthday(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friend_birthdays')
    name = models.CharField(max_length=100)
    relation = models.CharField(max_length=100)
    birthday = models.DateField()

    def __str__(self):
        return f"{self.name} ({self.relation}) - {self.birthday}"

class WishMessage(models.Model):
    message = models.TextField()

    def __str__(self):
        return self.message[:50] + '...'



class Country(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='countries')
    country = models.CharField(max_length=100, blank=True, null=True, default="")

    def __str__(self):
        return f"{self.user.email} - {self.country}" if self.user else self.country