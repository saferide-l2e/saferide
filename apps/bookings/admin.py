from django.contrib import admin

from .models import BoardingCredential, Booking, WaitlistEntry


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("passenger", "departure", "status", "created_at", "expires_at", "checked_in_at")
    list_filter = ("status",)
    search_fields = ("passenger__email", "passenger__display_name")
    readonly_fields = ("id", "created_at")


@admin.register(WaitlistEntry)
class WaitlistEntryAdmin(admin.ModelAdmin):
    list_display = ("passenger", "departure", "status", "joined_at", "offer_expires_at")
    list_filter = ("status",)
    search_fields = ("passenger__email",)
    readonly_fields = ("id", "joined_at")


@admin.register(BoardingCredential)
class BoardingCredentialAdmin(admin.ModelAdmin):
    list_display = ("booking", "issued_at", "consumed_at", "revoked_at")
    list_filter = ("consumed_at", "revoked_at")
    readonly_fields = ("id", "code_hash", "issued_at")
