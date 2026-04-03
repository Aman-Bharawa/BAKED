from django.contrib import admin

from .models import Dish


@admin.register(Dish)
class DishAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "chef",
        "price",
        "meal_slot",
        "estimated_calories",
        "health_score",
        "quantity_available",
        "is_published",
        "is_sold_out",
    )
    list_filter = ("meal_slot", "is_published", "is_sold_out", "is_veg", "is_keto", "is_high_protein", "is_low_calorie", "chef__location_name")
    search_fields = ("name", "chef__email", "chef__location_name")
