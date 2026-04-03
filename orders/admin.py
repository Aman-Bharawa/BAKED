from django.contrib import admin

from .models import Notification, Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "dish", "resident", "chef", "rider", "quantity", "total_price", "status")
    list_filter = ("status", "chef__location_name")
    search_fields = ("dish__name", "resident__email", "chef__email")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "recipient", "title", "order", "is_read", "created_at")
    list_filter = ("is_read",)
    search_fields = ("recipient__email", "title", "message")
