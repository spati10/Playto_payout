import threading
import uuid
from django.test import TransactionTestCase
from rest_framework.test import APIClient
from apps.ledger.models import LedgerEntry, LedgerEntryType
from apps.merchants.models import BankAccount, Merchant, MerchantBalance
from apps.payouts.models import Payout

class ConcurrencyTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.merchant = Merchant.objects.create(name="Concurrent Merchant", email="concurrent@example.com")
        self.bank = BankAccount.objects.create(
            merchant=self.merchant,
            account_holder_name="Concurrent Merchant",
            bank_name="ICICI",
            account_number="999900001111",
            ifsc_code="ICIC0002222",
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

    def _make_request(self, results, slot):
        client = APIClient()
        response = client.post(
            "/api/v1/payouts/",
            {
                "merchant_id": str(self.merchant.id),
                "bank_account_id": str(self.bank.id),
                "amount_paise": 6000,
            },
            format="json",
            HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()),
        )
        results[slot] = response.status_code

    def test_only_one_of_two_simultaneous_payouts_succeeds(self):
        results = {}

        t1 = threading.Thread(target=self._make_request, args=(results, 1))
        t2 = threading.Thread(target=self._make_request, args=(results, 2))

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        assert sorted(results.values()) == [400, 201]
        assert Payout.objects.count() == 1