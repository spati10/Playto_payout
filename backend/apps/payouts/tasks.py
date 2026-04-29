import random
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from .constants import PayoutStatus
from .models import Payout
from .services import (
    complete_payout,
    fail_payout_and_release_funds,
    move_payout_to_processing,
)


def simulate_bank_outcome():
    return random.choices(
        ["success", "failure", "hang"],
        weights=[70, 20, 10],
        k=1,
    )[0]

MAX_ATTEMPTS = 3

@shared_task(bind=True, max_retries=3)
def process_payout(self, payout_id):
    payout = Payout.objects.get(id=payout_id)

    if payout.status == PayoutStatus.PENDING:
        transition_payout(payout.id, PayoutStatus.PROCESSING)

    outcome = random.choices(
        ["completed", "failed", "stuck"],
        weights=[70, 20, 10],
        k=1,
    )[0]

    if outcome == "completed":
        transition_payout(payout.id, PayoutStatus.COMPLETED)
        return

    if outcome == "failed":
        transition_payout(payout.id, PayoutStatus.FAILED, "Settlement failed")
        return

    payout.refresh_from_db()
    payout.attempts += 1
    payout.save(update_fields=["attempts", "updated_at"])

    if payout.attempts >= MAX_ATTEMPTS:
        transition_payout(payout.id, PayoutStatus.FAILED, "Timed out after retries")
        return

    countdown = 2 ** payout.attempts
    raise self.retry(countdown=countdown)


@shared_task
def process_pending_payouts():
    now = timezone.now()

    payout_ids = list(
        Payout.objects.filter(
            status=PayoutStatus.PENDING,
        ).filter(
            next_retry_at__isnull=True
        ) | Payout.objects.filter(
            status=PayoutStatus.PENDING,
            next_retry_at__lte=now,
        ).values_list("id", flat=True)[:20]
    )

    for payout_id in payout_ids:
        process_single_payout.delay(str(payout_id))


@shared_task
def process_single_payout(payout_id):
    payout = Payout.objects.get(pk=payout_id)

    if payout.status != PayoutStatus.PENDING:
        return

    payout = move_payout_to_processing(payout.id)

    outcome = simulate_bank_outcome()

    if outcome == "success":
        complete_payout(payout.id)

    elif outcome == "failure":
        fail_payout_and_release_funds(
            payout.id,
            reason="Simulated bank failure",
        )

    else:
        return


@shared_task
def retry_stuck_payouts():
    cutoff = timezone.now() - timedelta(seconds=30)

    stuck_payouts = Payout.objects.filter(
        status=PayoutStatus.PROCESSING,
        processing_started_at__lt=cutoff,
    )

    for payout in stuck_payouts:
        if payout.attempts >= 3:
            fail_payout_and_release_funds(
                payout.id,
                reason="Max retries exceeded",
            )
            continue

        payout.status = PayoutStatus.FAILED
        payout.failure_reason = "Processing timeout"
        payout.failed_at = timezone.now()
        payout.save(update_fields=["status", "failure_reason", "failed_at", "updated_at"])

        fail_payout_and_release_funds(
            payout.id,
            reason="Processing timeout",
        )

@shared_task
def requeue_stuck_payouts():
    cutoff = timezone.now() - timedelta(seconds=30)

    stuck_ids = list(
        Payout.objects.filter(
            status=PayoutStatus.PROCESSING,
            updated_at__lt=cutoff,
            attempts__lt=MAX_ATTEMPTS,
        ).values_list("id", flat=True)
    )

    for payout_id in stuck_ids:
        process_payout.delay(str(payout_id))

    terminal_ids = list(
        Payout.objects.filter(
            status=PayoutStatus.PROCESSING,
            updated_at__lt=cutoff,
            attempts__gte=MAX_ATTEMPTS,
        ).values_list("id", flat=True)
    )

    for payout_id in terminal_ids:
        transition_payout(payout_id, PayoutStatus.FAILED, "Timed out after retries")