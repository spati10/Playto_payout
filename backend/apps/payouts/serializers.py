from rest_framework import serializers
from .models import Payout


class CreatePayoutSerializer(serializers.Serializer):
    merchant_id = serializers.UUIDField()
    bank_account_id = serializers.UUIDField()
    amount_paise = serializers.IntegerField(min_value=1)


class PayoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payout
        fields = [
            "id",
            "merchant",
            "bank_account",
            "amount_paise",
            "status",
            "failure_reason",
            "attempts",
            "created_at",
            "updated_at",
        ]