from django.db import models

class PayoutStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PROCESSING = "processing", "Processing"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"

ALLOWED_TRANSITIONS = {
    PayoutStatus.PENDING: {PayoutStatus.PROCESSING},
    PayoutStatus.PROCESSING: {PayoutStatus.COMPLETED, PayoutStatus.FAILED},
    PayoutStatus.COMPLETED: set(),
    PayoutStatus.FAILED: set(),
}