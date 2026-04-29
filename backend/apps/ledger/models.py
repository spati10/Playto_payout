import uuid
from django.db import models

class LedgerEntryType(models.TextChoices):
    CREDIT = "credit", "Credit"
    HOLD = "hold", "Hold"
    DEBIT = "debit", "Debit"
    RELEASE = "release", "Release"

class LedgerEntry(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    merchant = models.ForeignKey('merchants.Merchant', on_delete=models.CASCADE, related_name="ledger_entries")
    entry_type = models.CharField(max_length=20, choices=LedgerEntryType.choices)
    amount_paise = models.BigIntegerField()
    reference_type = models.CharField(max_length=50)
    reference_id = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["merchant", "created_at"]),
            models.Index(fields=["reference_type", "reference_id"]),
        ]