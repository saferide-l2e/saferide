from django.contrib import admin

from .models import DriverProfile, Vehicle


@admin.register(DriverProfile)
class DriverProfileAdmin(admin.ModelAdmin):
    list_display = ("safe_display_name", "user", "licence_status")
    list_filter = ("licence_status",)
    search_fields = ("public_display_name", "user__email")


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = (
        "plate_display",
        "vehicle_type",
        "seat_capacity",
        "driver",
        "approval_status",
    )
    list_filter = ("approval_status", "vehicle_type")
    search_fields = ("plate_display", "plate_normalized", "driver__user__email")
    readonly_fields = ("id", "plate_normalized")
