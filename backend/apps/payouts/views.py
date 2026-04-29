from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from apps.merchants.models import Merchant, BankAccount
from .models import Payout
from .serializers import CreatePayoutSerializer, PayoutSerializer
from .services import create_payout_request


class CreatePayoutView(APIView):
    def post(self, request):
        serializer = CreatePayoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        idempotency_key = request.headers.get("Idempotency-Key")
        if not idempotency_key:
            return Response({"detail": "Missing Idempotency-Key header"}, status=400)

        merchant = get_object_or_404(Merchant, id=serializer.validated_data["merchant_id"])
        bank_account = get_object_or_404(
            BankAccount,
            id=serializer.validated_data["bank_account_id"],
            merchant=merchant,
            is_active=True,
        )

        response_body, response_code = create_payout_request(
            merchant=merchant,
            bank_account=bank_account,
            amount_paise=serializer.validated_data["amount_paise"],
            idempotency_key=idempotency_key,
        )
        return Response(response_body, status=response_code)


class PayoutDetailView(APIView):
    def get(self, request, payout_id):
        payout = get_object_or_404(Payout, id=payout_id)
        return Response(PayoutSerializer(payout).data)