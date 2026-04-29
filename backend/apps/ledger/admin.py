from django.contrib import admin
from .models import LedgerEntry

@admin.register(LedgerEntry)
class LedgerEntryAdmin(admin.ModelAdmin):
    list_display = ["merchant", "entry_type", "amount_paise", "reference_type", "created_at"]
    list_filter = ["entry_type", "reference_type", "created_at"]
    readonly_fields = ["created_at"]