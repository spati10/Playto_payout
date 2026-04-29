from django.contrib import admin
from .models import IdempotencyKey

@admin.register(IdempotencyKey)
class IdempotencyKeyAdmin(admin.ModelAdmin):
    list_display = ["merchant", "key", "response_code", "is_in_progress", "expires_at"]
    list_filter = ["is_in_progress", "response_code"]
    readonly_fields = ["created_at", "expires_at"]