# EXPLAINER

This project is a minimal payout engine for merchants who accumulate INR balance and request withdrawals to Indian bank accounts. The focus of the implementation is not UI polish. The focus is money integrity, race-condition safety, idempotent API behavior, and payout lifecycle correctness.

## 1. The Ledger

The system stores all money in paise as integers using `BigIntegerField`. I modeled the ledger as immutable entries because payout systems need an auditable trail of how money moved, not just a final balance number.

### Balance calculation query

```python
from django.db.models import Sum, Case, When, Value, BigIntegerField
from django.db.models.functions import Coalesce
from apps.ledger.models import LedgerEntryType

merchant.ledger_entries.aggregate(
    total=Coalesce(
        Sum(
            Case(
                When(entry_type=LedgerEntryType.CREDIT, then="amount_paise"),
                When(entry_type=LedgerEntryType.RELEASE, then="amount_paise"),
                When(entry_type=LedgerEntryType.HOLD, then=Value(-1) * "amount_paise"),
                When(entry_type=LedgerEntryType.DEBIT, then=Value(-1) * "amount_paise"),
                output_field=BigIntegerField(),
            )
        ),
        0,
    )
)["total"]
```

### Why this model

- `credit` means customer funds became available to the merchant.
- `hold` means funds are reserved for a payout request but not yet settled.
- `debit` means the payout finalized successfully.
- `release` means a failed payout returned reserved funds back to availability.

I chose this instead of directly editing a single balance field with no journal because the challenge is about data integrity. A ledger lets me explain every paise movement and verify the invariant that ledger movement and displayed balances agree.

I also keep a `MerchantBalance` aggregate row for fast reads and safe locking during payout creation. The ledger is the audit trail. The balance row is the operational state.

## 2. The Lock

The bug I wanted to avoid was the classic check-then-deduct race:

- Request A reads available balance = 100
- Request B reads available balance = 100
- Both try to create a 60 payout
- Both succeed
- Merchant is overdrawn

The exact code that prevents that is below.

```python
@transaction.atomic
def create_payout_request(*, merchant, bank_account, amount_paise: int, idempotency_key: str):
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
```

### What database primitive it relies on

It relies on `SELECT ... FOR UPDATE`, exposed in Django as `select_for_update()`. That acquires a row-level lock inside a database transaction. If two payout requests hit the same merchant balance at the same time, the second request waits until the first transaction completes.

I also used `F()` expressions so the arithmetic happens inside PostgreSQL, not in Python on already-fetched values. That matters because the challenge specifically calls out Python-level arithmetic on fetched rows as a common failure mode.

## 3. The Idempotency

The API uses a merchant-scoped idempotency table with a unique constraint on `(merchant, key)`. Every payout creation request stores:

- merchant
- idempotency key
- request hash
- response code
- response body
- expiry time
- whether the first request is still in progress

### How the system knows it has seen a key before

It tries to insert a new row first. If that insert fails because of the unique constraint, the code loads the existing row for that merchant and key.

```python
class IdempotencyKey(models.Model):
    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE, related_name="idempotency_keys")
    key = models.CharField(max_length=128)
    request_hash = models.CharField(max_length=64)
    response_code = models.PositiveIntegerField(null=True, blank=True)
    response_body = models.JSONField(null=True, blank=True)
    is_in_progress = models.BooleanField(default=True)
    expires_at = models.DateTimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["merchant", "key"], name="uniq_idempotency_key_per_merchant")
        ]
```

### What happens if the first request is still in flight

The second request finds the existing idempotency row. Then it checks:

- if the key is expired, reject it
- if the request hash is different, reject it because the key is being reused with a different payload
- if `response_body` already exists, return the exact same stored response
- if the original request is still in progress, reject with “Original request is still in flight”

That logic is here:

```python
except IntegrityError:
    idem = IdempotencyKey.objects.select_for_update().get(
        merchant=merchant,
        key=idempotency_key,
    )

    if idem.expires_at < timezone.now():
        raise ValidationError("Idempotency key expired")

    if idem.request_hash != request_hash:
        raise ValidationError("Idempotency key reused with a different payload")

    if idem.response_body is not None:
        return idem.response_body, idem.response_code

    raise ValidationError("Original request is still in flight")
```

This design gives replay safety and prevents duplicate payouts even if the client retries because of a timeout or flaky network.

## 4. The State Machine

The allowed transitions are:

- `pending -> processing`
- `processing -> completed`
- `processing -> failed`

Anything else is illegal.

```python
ALLOWED_TRANSITIONS = {
    PayoutStatus.PENDING: {PayoutStatus.PROCESSING},
    PayoutStatus.PROCESSING: {PayoutStatus.COMPLETED, PayoutStatus.FAILED},
    PayoutStatus.COMPLETED: set(),
    PayoutStatus.FAILED: set(),
}
```

The explicit check that blocks `failed -> completed` is:

```python
def ensure_valid_transition(current_status: str, next_status: str) -> None:
    if next_status not in ALLOWED_TRANSITIONS[current_status]:
        raise ValidationError(f"Illegal state transition: {current_status} -> {next_status}")
```

That function is called before every state transition, including completion and failure paths.

For example, completion does this first:

```python
@transaction.atomic
def complete_payout(payout_id):
    payout = Payout.objects.select_for_update().get(pk=payout_id)
    ensure_valid_transition(payout.status, PayoutStatus.COMPLETED)
```

A failed payout returning funds must happen atomically with the status change, so the failure path runs inside one transaction and does three things together:

1. lock the payout
2. return held funds back to available balance
3. write a `release` ledger entry
4. mark the payout as `failed`

That means the system cannot end up in a half-failed, half-refunded state.

## 5. The AI Audit

One subtle bug I caught from an AI-generated approach was this pattern:

```python
balance = MerchantBalance.objects.get(merchant=merchant)

if balance.available_balance_paise >= amount_paise:
    balance.available_balance_paise -= amount_paise
    balance.held_balance_paise += amount_paise
    balance.save()
```

At first glance this looks fine. It is not safe. The bug is that two concurrent requests can both read the same `available_balance_paise` before either save happens. That creates an overdraft race.

### What I replaced it with

```python
@transaction.atomic
def create_payout_request(*, merchant, bank_account, amount_paise: int, idempotency_key: str):
    balance = MerchantBalance.objects.select_for_update().get(merchant=merchant)

    if balance.available_balance_paise < amount_paise:
        raise ValidationError("Insufficient available balance")

    MerchantBalance.objects.filter(pk=balance.pk).update(
        available_balance_paise=F("available_balance_paise") - amount_paise,
        held_balance_paise=F("held_balance_paise") + amount_paise,
    )
```

### Why the replacement is correct

- `transaction.atomic()` makes the whole operation one transaction
- `select_for_update()` locks the merchant balance row
- `F()` expressions move the arithmetic into the database
- the balance check and mutation now happen under lock, not on stale Python state

That was the main place where blindly trusting generated code would have produced a payout engine that looked correct in normal testing but failed under concurrent traffic.

## Tradeoffs

A few decisions were intentionally simple:

- The frontend uses polling every 5 seconds instead of websockets. That is enough for this challenge and keeps complexity focused on the payout engine.
- I used a balance aggregate row plus ledger, instead of ledger-only reads for every request. That makes locking easier and keeps the audit trail explicit.
- I seeded only 3 merchants because the prompt asked for 2 to 3, and the point is correctness, not volume simulation.

## What I would improve next

If this were extended beyond the challenge, the next changes would be:

- a dedicated webhook/event table for payout lifecycle events
- scheduled Celery beat jobs for stuck payout retries
- stronger API authentication per merchant
- database constraints for non-negative balances
- structured audit logs for operator actions