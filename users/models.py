from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

def user_profile_upload_path(instance, filename):
    return f"profile_pics/user_{instance.id}/{filename}"

class User(AbstractUser):
    username = models.CharField(max_length=150, unique=False, blank=True, null=True)
    first_name = models.CharField(max_length=10, blank=True, null=True)
    last_name = models.CharField(max_length=10, blank=True, null=True)

    email = models.EmailField(unique=True, blank=False)
    otp = models.CharField(max_length=6, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    otp_created_at = models.DateTimeField(null=True, blank=True, default=timezone.now)
    otp_request_count = models.IntegerField(default=0)
    otp_request_reset_time = models.DateTimeField(blank=True, null=True)

    profile_picture = models.ImageField(
        upload_to=user_profile_upload_path,
        null=True,
        blank=True
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email
