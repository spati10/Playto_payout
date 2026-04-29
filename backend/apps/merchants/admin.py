from django.contrib import admin
from .models import BankAccount, Merchant, MerchantBalance

@admin.register(Merchant)
class MerchantAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["name", "email"]

@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ["merchant", "bank_name", "masked_account_number", "is_active"]
    list_filter = ["is_active", "bank_name"]
    readonly_fields = ["masked_account_number"]

@admin.register(MerchantBalance)
class MerchantBalanceAdmin(admin.ModelAdmin):
    list_display = ["merchant", "available_balance_paise", "held_balance_paise"]
    readonly_fields = ["updated_at"]