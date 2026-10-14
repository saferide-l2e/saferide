from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("email", "display_name", "role", "is_staff")
    fieldsets = BaseUserAdmin.fieldsets + (
        ("SafeRide Profile", {"fields": ("role", "display_name")}),
    )
