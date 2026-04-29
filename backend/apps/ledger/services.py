from django.db.models import Sum, Case, When, IntegerField, F
from .models import LedgerEntry

def get_balance(merchant_id):
    result = LedgerEntry.objects.filter(merchant_id=merchant_id).aggregate(
        balance=Sum(
            Case(
                When(type="credit", then=F("amount_paise")),
                When(type="debit", then=-1 * F("amount_paise")),
                output_field=IntegerField(),
            )
        )
    )
    return result["balance"] or 0