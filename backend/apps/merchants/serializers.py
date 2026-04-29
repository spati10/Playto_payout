from rest_framework import serializers
from .models import BankAccount, Merchant

class BankAccountSerializer(serializers.ModelSerializer):
    masked_account_number = serializers.CharField(read_only=True)

    class Meta:
        model = BankAccount
        fields = [
            "id",
            "bank_name",
            "account_holder_name",
            "masked_account_number",
            "ifsc_code",
            "is_active",
        ]
class MerchantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Merchant
        fields = ["id", "name", "email"]