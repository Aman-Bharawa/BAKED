from django.conf import settings
from django.db import models


class Dish(models.Model):
    class MealSlot(models.TextChoices):
        BREAKFAST = "breakfast", "Breakfast"
        LUNCH = "lunch", "Lunch"
        DINNER = "dinner", "Dinner"

    chef = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="dishes",
    )
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    meal_slot = models.CharField(
        max_length=20,
        choices=MealSlot.choices,
        default=MealSlot.LUNCH,
    )
    main_ingredient_amount = models.PositiveIntegerField(blank=True, null=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    quantity_available = models.PositiveIntegerField()
    media = models.FileField(upload_to="dish_media/", blank=True, null=True)
    estimated_calories = models.PositiveIntegerField(default=0)
    health_score = models.DecimalField(max_digits=3, decimal_places=1, default=0)
    nutrition_notes = models.TextField(blank=True)
    is_veg = models.BooleanField(default=False)
    is_keto = models.BooleanField(default=False)
    is_high_protein = models.BooleanField(default=False)
    is_low_calorie = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False)
    is_sold_out = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} by {self.chef.email}"
