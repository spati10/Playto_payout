from django.contrib import admin
from .models import Payout

@admin.register(Payout)
class PayoutAdmin(admin.ModelAdmin):
    list_display = ["id", "merchant", "amount_paise", "status", "attempts", "created_at"]
    list_filter = ["status", "attempts", "created_at"]
    readonly_fields = ["created_at", "updated_at"]
    search_fields = ["merchant__name", "id"]