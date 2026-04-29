import os
import django
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.ledger.models import LedgerEntry, LedgerEntryType
from apps.merchants.models import BankAccount, Merchant, MerchantBalance

def run():
    """Seed demo merchants with realistic balances and bank accounts."""
    seed_merchants = [
        {
            "name": "Acme Agency",
            "email": "acme@example.com",
            "amount": 250000,  # ₹2500
            "bank_name": "HDFC Bank",
            "account_number": "123456789001",
            "ifsc": "HDFC0001234",
        },
        {
            "name": "Pixel Studio", 
            "email": "pixel@example.com",
            "amount": 185000,  # ₹1850
            "bank_name": "ICICI Bank",
            "account_number": "123456789002",
            "ifsc": "ICIC0005678",
        },
        {
            "name": "Growth Forge",
            "email": "growth@example.com", 
            "amount": 92000,   # ₹920
            "bank_name": "Axis Bank",
            "account_number": "123456789003",
            "ifsc": "UTIB0001122",
        },
    ]

    created = []
    
    for row in seed_merchants:
        merchant, created_merchant = Merchant.objects.get_or_create(
            email=row["email"],
            defaults={"name": row["name"]},
        )
        
        balance, created_balance = MerchantBalance.objects.get_or_create(
            merchant=merchant,
            defaults={
                "available_balance_paise": row["amount"],
                "held_balance_paise": 0,
            },
        )
        
        account, created_account = BankAccount.objects.get_or_create(
            merchant=merchant,
            account_number=row["account_number"],
            defaults={
                "account_holder_name": row["name"],
                "bank_name": row["bank_name"],
                "ifsc_code": row["ifsc"],
                "is_active": True,
            },
        )
        
        ledger_entry, created_ledger = LedgerEntry.objects.get_or_create(
            merchant=merchant,
            reference_type="seed_credit",
            defaults={
                "entry_type": LedgerEntryType.CREDIT,
                "amount_paise": row["amount"],
            },
        )
        
        if any([created_merchant, created_balance, created_account, created_ledger]):
            created.append(row["name"])

    if created:
        print(f"Seeded merchants: {', '.join(created)}")
    else:
        print("Demo data already exists.")

if __name__ == "__main__":
    run()