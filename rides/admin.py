from django.contrib import admin

from .models import Ride, RideEvent


@admin.register(Ride)
class RideAdmin(admin.ModelAdmin):
    list_display = ("id_ride", "status", "id_rider", "id_driver", "pickup_time")
    list_filter = ("status", "pickup_time")
    search_fields = (
        "id_rider__email",
        "id_rider__first_name",
        "id_driver__email",
        "id_driver__first_name",
    )
    date_hierarchy = "pickup_time"


@admin.register(RideEvent)
class RideEventAdmin(admin.ModelAdmin):
    list_display = ("id_ride_event", "id_ride", "description", "created_at")
    list_filter = ("created_at",)
    search_fields = ("description",)
