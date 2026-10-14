from django.contrib import admin, messages
from django.core.exceptions import ValidationError

from . import services
from .models import Verification


@admin.register(Verification)
class VerificationAdmin(admin.ModelAdmin):
    list_display = ("user", "status", "submitted_at", "reviewed_by", "reviewed_at")
    list_filter = ("status",)
    search_fields = ("user__email", "user__display_name")
    readonly_fields = ("id", "submitted_at", "reviewed_by", "reviewed_at")
    actions = ("approve_selected", "reject_selected", "suspend_selected")

    @admin.action(description="Approve selected (demo verification)")
    def approve_selected(self, request, queryset):
        self._run(request, queryset, services.approve)

    @admin.action(description="Reject selected")
    def reject_selected(self, request, queryset):
        self._run(request, queryset, services.reject)

    @admin.action(description="Suspend selected")
    def suspend_selected(self, request, queryset):
        self._run(request, queryset, services.suspend)

    def _run(self, request, queryset, action):
        done = 0
        for verification in queryset:
            try:
                action(verification, request.user, note="Admin decision")
                done += 1
            except ValidationError as exc:
                self.message_user(request, f"{verification}: {exc}", level=messages.ERROR)
        self.message_user(request, f"{done} verification record(s) updated.")
