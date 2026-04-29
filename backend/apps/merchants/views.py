from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.ledger.models import LedgerEntry, LedgerEntryType
from apps.payouts.models import Payout
from .models import Merchant, MerchantBalance
from .serializers import BankAccountSerializer, MerchantSerializer


class MerchantDashboardView(APIView):
    def get(self, request, merchant_id):
        try:
            merchant = get_object_or_404(Merchant, id=merchant_id)

            balance, _ = MerchantBalance.objects.get_or_create(
                merchant=merchant,
                defaults={
                    "available_balance_paise": 0,
                    "held_balance_paise": 0,
                },
            )
            
            debits_total = merchant.ledger_entries.filter(
                merchant = merchant,
                entry_type = LedgerEntryType.DEBIT

            )

            credits_total = LedgerEntry.objects.filter(
                merchant=merchant,
                entry_type=LedgerEntryType.CREDIT
            ).aggregate(total=Coalesce(Sum("amount_paise"), 0))["total"]

            ledger_rows = list(
                LedgerEntry.objects.filter(merchant=merchant)
                .values(
                    "id",
                    "entry_type",
                    "amount_paise",
                    "reference_type",
                    "reference_id",
                    "created_at",
                )[:10]
            )

            payouts = list(
                Payout.objects.filter(merchant=merchant)
                .values(
                    "id",
                    "amount_paise",
                    "status",
                    "attempts",
                    "failure_reason",
                    "created_at",
                )[:20]
            )

            bank_accounts = merchant.bank_accounts.filter(is_active=True)

            return Response({
                "merchant": MerchantSerializer(merchant).data,
                "available_balance_paise": balance.available_balance_paise,
                "held_balance_paise": balance.held_balance_paise,
                "total_credits_paise": credits_total,
                "ledger": ledger_rows,
                "payouts": payouts,
                "bank_accounts": BankAccountSerializer(bank_accounts, many=True).data,
            })

        except Exception as e:
            return Response({"error": str(e)}, status=500)