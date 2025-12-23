from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from .queryset import RideEventQuerySet, RideQuerySet

LATITUDE_MIN = -90
LATITUDE_MAX = 90
LONGITUDE_MIN = -180
LONGITUDE_MAX = 180

LATITUDE_VALIDATORS = [MinValueValidator(LATITUDE_MIN), MaxValueValidator(LATITUDE_MAX)]
LONGITUDE_VALIDATORS = [
    MinValueValidator(LONGITUDE_MIN),
    MaxValueValidator(LONGITUDE_MAX),
]


class RideStatus(models.TextChoices):
    EN_ROUTE = "en-route", "En Route"
    PICKUP = "pickup", "Pickup"
    DROPOFF = "dropoff", "Dropoff"


class RideManager(models.Manager.from_queryset(RideQuerySet)):
    pass


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

    pickup_latitude = models.FloatField(validators=LATITUDE_VALIDATORS)
    pickup_longitude = models.FloatField(validators=LONGITUDE_VALIDATORS)

    dropoff_latitude = models.FloatField(validators=LATITUDE_VALIDATORS)
    dropoff_longitude = models.FloatField(validators=LONGITUDE_VALIDATORS)

    # unsure if this is estimated pickup time or actual pickup time (if so, this should be nullable)
    pickup_time = models.DateTimeField(db_index=True)

    objects = RideManager()

    class Meta:
        ordering = ["id_ride"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    pickup_latitude__gte=LATITUDE_MIN, pickup_latitude__lte=LATITUDE_MAX
                ),
                name="ride_pickup_latitude_range",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    pickup_longitude__gte=LONGITUDE_MIN,
                    pickup_longitude__lte=LONGITUDE_MAX,
                ),
                name="ride_pickup_longitude_range",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    dropoff_latitude__gte=LATITUDE_MIN,
                    dropoff_latitude__lte=LATITUDE_MAX,
                ),
                name="ride_dropoff_latitude_range",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    dropoff_longitude__gte=LONGITUDE_MIN,
                    dropoff_longitude__lte=LONGITUDE_MAX,
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


class RideEventManager(models.Manager.from_queryset(RideEventQuerySet)):
    pass


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
