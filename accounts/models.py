from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        CHEF = "chef", "HomeChef"
        RESIDENT = "resident", "Resident"
        RIDER = "rider", "Rider"

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices)
    location_name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=20, blank=True)
    vehicle_details = models.CharField(max_length=150, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, default=0)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, default=0)
    is_available = models.BooleanField(
        default=False,
        help_text="Used only for riders to indicate availability for delivery jobs.",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "role", "location_name"]

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"
