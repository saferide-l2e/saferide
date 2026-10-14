from django.contrib import admin

from .models import VerificationStatus


@admin.register(VerificationStatus)
class VerificationStatusAdmin(admin.ModelAdmin):
    list_display = ("user", "status", "reviewed_by", "reviewed_at", "updated_at")
    readonly_fields = ("created_at", "updated_at")
    list_filter = ("status",)
