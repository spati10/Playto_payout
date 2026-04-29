import hashlib
import json
from datetime import timedelta

from django.db import IntegrityError, transaction
from django.db.models import F
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import ValidationError

from apps.idempotency.models import IdempotencyKey
from apps.ledger.models import LedgerEntry, LedgerEntryType
from apps.merchants.models import MerchantBalance
from .constants import ALLOWED_TRANSITIONS, PayoutStatus
from .models import Payout

LEGAL_TRANSITIONS = {
    PayoutStatus.PENDING: {PayoutStatus.PROCESSING},
    PayoutStatus.PROCESSING: {PayoutStatus.COMPLETED, PayoutStatus.FAILED},
    PayoutStatus.COMPLETED: set(),
    PayoutStatus.FAILED: set(),
}

MAX_RETRIES = 3

def assert_transition_allowed(current, new):
    if new not in LEGAL_TRANSITIONS[current]:
        raise ValidationError(f"Illegal payout transition: {current} -> {new}")

def make_request_hash(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()


def ensure_valid_transition(current_status: str, next_status: str) -> None:
    if next_status not in ALLOWED_TRANSITIONS[current_status]:
        raise ValidationError(f"Illegal state transition: {current_status} -> {next_status}")


@transaction.atomic
def create_payout_request(*, merchant, bank_account, amount_paise: int, idempotency_key: str):
    if amount_paise <= 0:
        raise ValidationError("amount_paise must be greater than zero")

    payload = {
        "bank_account_id": str(bank_account.id),
        "amount_paise": amount_paise,
    }
    request_hash = make_request_hash(payload)

    try:
        idem = IdempotencyKey.objects.create(
            merchant=merchant,
            key=idempotency_key,
            request_hash=request_hash,
            expires_at=timezone.now() + timedelta(hours=24),
            is_in_progress=True,
        )
    except IntegrityError:
        idem = IdempotencyKey.objects.select_for_update().get(
            merchant=merchant,
            key=idempotency_key,
        )

        if idem.expires_at < timezone.now():
            raise ValidationError("Idempotency key expired")

        if idem.request_hash != request_hash:
            raise ValidationError("Idempotency key reused with different payload")

        if idem.response_body is not None:
            return idem.response_body, idem.response_code

        raise ValidationError("Original request is still in progress")

    balance = MerchantBalance.objects.select_for_update().get(merchant=merchant)

    if balance.available_balance_paise < amount_paise:
        response_body = {"detail": "Insufficient available balance"}
        idem.response_code = status.HTTP_400_BAD_REQUEST
        idem.response_body = response_body
        idem.is_in_progress = False
        idem.save(update_fields=["response_code", "response_body", "is_in_progress"])
        return response_body, status.HTTP_400_BAD_REQUEST

    MerchantBalance.objects.filter(pk=balance.pk).update(
        available_balance_paise=F("available_balance_paise") - amount_paise,
        held_balance_paise=F("held_balance_paise") + amount_paise,
    )

    payout = Payout.objects.create(
        merchant=merchant,
        bank_account=bank_account,
        amount_paise=amount_paise,
        status=PayoutStatus.PENDING,
    )

    LedgerEntry.objects.create(
        merchant=merchant,
        entry_type=LedgerEntryType.HOLD,
        amount_paise=amount_paise,
        reference_type="payout",
        reference_id=payout.id,
    )

    response_body = {
        "id": str(payout.id),
        "status": payout.status,
        "amount_paise": payout.amount_paise,
        "bank_account_id": str(bank_account.id),
        "created_at": payout.created_at.isoformat(),
    }

    idem.response_code = status.HTTP_201_CREATED
    idem.response_body = response_body
    idem.is_in_progress = False
    idem.save(update_fields=["response_code", "response_body", "is_in_progress"])

    return response_body, status.HTTP_201_CREATED


@transaction.atomic
def move_payout_to_processing(payout_id):
    payout = Payout.objects.select_for_update().get(pk=payout_id)
    ensure_valid_transition(payout.status, PayoutStatus.PROCESSING)

    payout.status = PayoutStatus.PROCESSING
    payout.processing_started_at = timezone.now()
    payout.attempts += 1
    payout.next_retry_at = None
    payout.save(update_fields=["status", "processing_started_at", "attempts", "next_retry_at", "updated_at"])
    return payout


@transaction.atomic
def complete_payout(payout_id):
    payout = Payout.objects.select_for_update().get(pk=payout_id)
    ensure_valid_transition(payout.status, PayoutStatus.COMPLETED)

    balance = MerchantBalance.objects.select_for_update().get(merchant=payout.merchant)
    MerchantBalance.objects.filter(pk=balance.pk).update(
        held_balance_paise=F("held_balance_paise") - payout.amount_paise
    )

    LedgerEntry.objects.create(
        merchant=payout.merchant,
        entry_type=LedgerEntryType.DEBIT,
        amount_paise=payout.amount_paise,
        reference_type="payout",
        reference_id=payout.id,
    )

    payout.status = PayoutStatus.COMPLETED
    payout.completed_at = timezone.now()
    payout.save(update_fields=["status", "completed_at", "updated_at"])
    return payout


@transaction.atomic
def fail_payout_and_release_funds(payout_id, reason="bank settlement failed"):
    payout = Payout.objects.select_for_update().get(pk=payout_id)
    ensure_valid_transition(payout.status, PayoutStatus.FAILED)

    balance = MerchantBalance.objects.select_for_update().get(merchant=payout.merchant)
    MerchantBalance.objects.filter(pk=balance.pk).update(
        available_balance_paise=F("available_balance_paise") + payout.amount_paise,
        held_balance_paise=F("held_balance_paise") - payout.amount_paise,
    )

    LedgerEntry.objects.create(
        merchant=payout.merchant,
        entry_type=LedgerEntryType.RELEASE,
        amount_paise=payout.amount_paise,
        reference_type="payout",
        reference_id=payout.id,
    )

    payout.status = PayoutStatus.FAILED
    payout.failure_reason = reason
    payout.failed_at = timezone.now()
    payout.save(update_fields=["status", "failure_reason", "failed_at", "updated_at"])
    return payout