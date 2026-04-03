from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("email", "username", "role", "location_name", "is_available", "is_staff")
    list_filter = ("role", "location_name", "is_available", "is_staff")
    ordering = ("email",)

    fieldsets = BaseUserAdmin.fieldsets + (
        (
            "Location HomeChef",
            {
                "fields": (
                    "role",
                    "location_name",
                    "phone_number",
                    "vehicle_details",
                    "latitude",
                    "longitude",
                    "is_available",
                )
            },
        ),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (
            "Location HomeChef",
            {
                "fields": (
                    "email",
                    "role",
                    "location_name",
                    "phone_number",
                    "vehicle_details",
                    "latitude",
                    "longitude",
                    "is_available",
                )
            },
        ),
    )
