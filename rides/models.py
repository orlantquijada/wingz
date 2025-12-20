from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class RideStatus(models.TextChoices):
    EN_ROUTE = "en-route", "En Route"
    PICKUP = "pickup", "Pickup"
    DROPOFF = "dropoff", "Dropoff"


class RideManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("id_rider", "id_driver")


class Ride(models.Model):
    id_ride = models.AutoField(primary_key=True)

    status = models.CharField(
        max_length=20,
        choices=RideStatus.choices,
        default=RideStatus.EN_ROUTE,
        db_index=True,
    )

    id_rider = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="rides_as_rider",
        db_column="id_rider",
    )
    id_driver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="rides_as_driver",
        db_column="id_driver",
    )

    pickup_latitude = models.FloatField()
    pickup_longitude = models.FloatField()

    dropoff_latitude = models.FloatField()
    dropoff_longitude = models.FloatField()

    pickup_time = models.DateTimeField(db_index=True)

    objects = RideManager()

    def __str__(self):
        return f"Ride {self.id_ride}: {self.status}"


class RideEventType(models.TextChoices):
    STATUS_EN_ROUTE = "Status changed to en-route"
    STATUS_PICKUP = "Status changed to pickup"
    STATUS_DROPOFF = "Status changed to dropoff"

    # we can still add more status here
    # DRIVER_CANCELLED = "Driver cancelled Ride"
    # RIDER_CANCELLED = "Rider cancelled Ride"


class RideEventManager(models.Manager):
    def recent(self, hours: int = 24):
        return self.get_queryset().filter(
            created_at__gte=timezone.now() - timedelta(hours=hours)
        )


class RideEvent(models.Model):
    id_ride_event = models.AutoField(primary_key=True)

    id_ride = models.ForeignKey(
        Ride,
        on_delete=models.CASCADE,
        related_name="ride_events",
        db_column="id_ride",
    )

    description = models.CharField(
        max_length=50,
        choices=RideEventType.choices,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    objects = RideEventManager()

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["id_ride", "created_at"], name="rideevent_ride_created_idx"
            ),
        ]

    def __str__(self):
        return f"RideEvent {self.id_ride_event}: {self.description}"
