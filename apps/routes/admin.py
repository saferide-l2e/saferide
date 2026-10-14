from django.contrib import admin

from .models import Route


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ("origin_name", "destination_name", "boarding_point", "is_active")
    list_filter = ("is_active",)
    search_fields = ("origin_name", "destination_name", "boarding_point")
