from django.contrib import admin

from .models import Departure


@admin.register(Departure)
class DepartureAdmin(admin.ModelAdmin):
    list_display = (
        "route",
        "driver",
        "vehicle",
        "scheduled_departure_at",
        "snapshot_capacity",
        "walk_in_count",
        "status",
    )
    list_filter = ("status", "route")
    search_fields = ("driver__email", "vehicle__plate_display", "route__origin_name")
    date_hierarchy = "scheduled_departure_at"
    readonly_fields = ("snapshot_capacity", "created_at", "updated_at")
