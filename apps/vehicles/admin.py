from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied

from . import services
from .models import DriverProfile, Vehicle


@admin.register(DriverProfile)
class DriverProfileAdmin(admin.ModelAdmin):
    list_display = ("display_name", "user", "licence_review_status")
    list_filter = ("licence_review_status",)
    search_fields = ("user__email", "user__display_name", "approved_display_name")

    @admin.action(description="Approve driver profile")
    def approve_drivers(self, request, queryset):
        from .models import ApprovalStatus

        for profile in queryset:
            profile.licence_review_status = ApprovalStatus.APPROVED
            profile.save(update_fields=["licence_review_status"])
        self.message_user(request, f"{queryset.count()} driver profile(s) approved.")


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ("plate_display", "vehicle_type", "capacity", "approval_status", "driver")
    list_filter = ("approval_status", "vehicle_type")
    search_fields = ("plate_display", "plate_normalized", "driver__user__email")
    actions = ("approve_vehicles", "reject_vehicles")

    @admin.action(description="Approve selected vehicles")
    def approve_vehicles(self, request, queryset):
        for vehicle in queryset:
            try:
                services.approve_vehicle(vehicle, request.user)
            except PermissionDenied as exc:
                self.message_user(request, str(exc), level=messages.ERROR)

    @admin.action(description="Reject selected vehicles")
    def reject_vehicles(self, request, queryset):
        for vehicle in queryset:
            try:
                services.reject_vehicle(vehicle, request.user)
            except PermissionDenied as exc:
                self.message_user(request, str(exc), level=messages.ERROR)
