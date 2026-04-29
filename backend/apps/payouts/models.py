import uuid
from django.db import models
from apps.merchants.models import Merchant, BankAccount
from .constants import PayoutStatus

LEGAL_TRANSITIONS = {
    PayoutStatus.PENDING: {PayoutStatus.PROCESSING},
    PayoutStatus.PROCESSING: {PayoutStatus.COMPLETED, PayoutStatus.FAILED},
    PayoutStatus.COMPLETED: set(),
    PayoutStatus.FAILED: set(),
}

class Payout(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE, related_name="payouts")
    bank_account = models.ForeignKey(BankAccount, on_delete=models.PROTECT, related_name="payouts")
    amount_paise = models.BigIntegerField()
    status = models.CharField(max_length=20, choices=PayoutStatus.choices, default=PayoutStatus.PENDING)
    failure_reason = models.CharField(max_length=255, blank=True, default="")
    attempts = models.PositiveSmallIntegerField(default=0)
    processing_started_at = models.DateTimeField(null=True, blank=True)
    next_retry_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["merchant", "created_at"]),
            models.Index(fields=["status", "next_retry_at"]),
        ]