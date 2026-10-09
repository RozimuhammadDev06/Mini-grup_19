from django.db import models
from apps.shop.models import Order


class Payment(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    fhp_payment_id = models.CharField(max_length=100, blank=True, null=True)
    fhp_status = models.IntegerField(blank=True, null=True)
    merchant_prepare_id = models.CharField(max_length=100, blank=True, null=True)
    merchant_confirm_id = models.CharField(max_length=100, blank=True, null=True)
    card_mask = models.CharField(max_length=30, blank=True, null=True)
    error_note = models.TextField(blank=True, null=True)
    prepared_at = models.DateTimeField(blank=True, null=True)
    confirmed_at = models.DateTimeField(blank=True, null=True)
    refunded_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment for Order #{self.order.number}"


class CardToken(models.Model):
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='card_tokens')
    card_token = models.CharField(max_length=255)
    card_number_masked = models.CharField(max_length=30)
    card_expire = models.CharField(max_length=10)
    status = models.CharField(max_length=20, default='pending')
    temporary = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Card {self.card_number_masked} ({self.user})"


class CallbackLog(models.Model):
    endpoint = models.CharField(max_length=50)
    raw_payload = models.JSONField()
    signature_valid = models.BooleanField(default=False)
    response_sent = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.endpoint} - {self.created_at}"