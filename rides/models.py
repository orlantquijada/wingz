from datetime import timedelta

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from .queryset import RideQuerySet


class RideStatus(models.TextChoices):
    EN_ROUTE = "en-route", "En Route"
    PICKUP = "pickup", "Pickup"
    DROPOFF = "dropoff", "Dropoff"


class RideManager(models.Manager.from_queryset(RideQuerySet)):
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

    pickup_latitude = models.FloatField(
        validators=[MinValueValidator(-90), MaxValueValidator(90)]
    )
    pickup_longitude = models.FloatField(
        validators=[MinValueValidator(-180), MaxValueValidator(180)]
    )

    dropoff_latitude = models.FloatField(
        validators=[MinValueValidator(-90), MaxValueValidator(90)]
    )
    dropoff_longitude = models.FloatField(
        validators=[MinValueValidator(-180), MaxValueValidator(180)]
    )

    # unsure if this is estimated pickup time or actual pickup time (if so, this should be nullable)
    pickup_time = models.DateTimeField(db_index=True)

    objects = RideManager()

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(pickup_latitude__gte=-90, pickup_latitude__lte=90),
                name="ride_pickup_latitude_range",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    pickup_longitude__gte=-180, pickup_longitude__lte=180
                ),
                name="ride_pickup_longitude_range",
            ),
            models.CheckConstraint(
                condition=models.Q(dropoff_latitude__gte=-90, dropoff_latitude__lte=90),
                name="ride_dropoff_latitude_range",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    dropoff_longitude__gte=-180, dropoff_longitude__lte=180
                ),
                name="ride_dropoff_longitude_range",
            ),
        ]

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
