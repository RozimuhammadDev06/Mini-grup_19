from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    full_name = models.CharField(max_length=255, blank=True, null=True)
    region = models.ForeignKey('shop.Region', on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username

    class Meta:
        app_label = 'users'


class UserOTPVerifications(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=10)
    attapts = models.PositiveIntegerField(default=0)
    resend_attapts = models.PositiveIntegerField(default=0)
    for_forget_password = models.BooleanField(default=False)
    for_forget_password_verified = models.BooleanField(default=False)
    expired_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"OTP for {self.user.username}"

    class Meta:
        app_label = 'users'


class UserOTPIDVerifications(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=10)
    attapts = models.PositiveIntegerField(default=0)
    expired_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"OTP ID for {self.user.username}"

    class Meta:
        app_label = 'users'


class ChangePasswordLogs(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    attapts = models.PositiveIntegerField(default=0)
    is_changed = models.BooleanField(default=False)
    expired_at = models.DateTimeField(null=True, blank=True)
    error_expired_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Password log: {self.user.username}"

    class Meta:
        app_label = 'users'


class ChangeEmailLogs(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    old_email = models.EmailField()
    new_email = models.EmailField()
    code = models.CharField(max_length=10)
    attapts = models.PositiveIntegerField(default=0)
    resend_attapts = models.PositiveIntegerField(default=0)
    is_changed = models.BooleanField(default=False)
    expired_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Email change: {self.old_email} -> {self.new_email}"

    class Meta:
        app_label = 'users'