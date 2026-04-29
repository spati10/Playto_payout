import uuid
from rest_framework.test import APITestCase
from apps.ledger.models import LedgerEntry, LedgerEntryType
from apps.merchants.models import BankAccount, Merchant, MerchantBalance
from apps.payouts.models import Payout

class IdempotencyTests(APITestCase):
    def setUp(self):
        self.merchant = Merchant.objects.create(name="Demo Merchant", email="demo@example.com")
        self.bank = BankAccount.objects.create(
            merchant=self.merchant,
            account_holder_name="Demo Merchant",
            bank_name="HDFC",
            account_number="111122223333",
            ifsc_code="HDFC0001111",
            is_active=True,
        )
        MerchantBalance.objects.create(
            merchant=self.merchant,
            available_balance_paise=10000,
            held_balance_paise=0,
        )
        LedgerEntry.objects.create(
            merchant=self.merchant,
            entry_type=LedgerEntryType.CREDIT,
            amount_paise=10000,
            reference_type="seed_credit",
        )

    def test_same_key_returns_same_response_and_single_payout(self):
        idem_key = str(uuid.uuid4())
        payload = {
            "merchant_id": str(self.merchant.id),
            "bank_account_id": str(self.bank.id),
            "amount_paise": 5000,
        }

        response_1 = self.client.post(
            "/api/v1/payouts/",
            payload,
            format="json",
            HTTP_IDEMPOTENCY_KEY=idem_key,
        )
        response_2 = self.client.post(
            "/api/v1/payouts/",
            payload,
            format="json",
            HTTP_IDEMPOTENCY_KEY=idem_key,
        )

        assert response_1.status_code == 201
        assert response_2.status_code == 201
        assert response_1.json() == response_2.json()
        assert Payout.objects.count() == 1