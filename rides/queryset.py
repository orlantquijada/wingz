from datetime import timedelta

from django.db import models
from django.db.models import Prefetch
from django.db.models.functions import Power, Sqrt
from django.utils import timezone


class RideEventQuerySet(models.QuerySet):
    def recent(self, hours: int = 24):
        return self.filter(created_at__gte=timezone.now() - timedelta(hours=hours))


class RideQuerySet(models.QuerySet):
    def with_rider_and_driver(self):
        return self.select_related("id_rider", "id_driver")

    def with_todays_ride_events(self):
        from .models import RideEvent  # avoid circular import

        return self.prefetch_related(
            Prefetch(
                "ride_events",
                queryset=RideEvent.objects.recent(),
                to_attr="todays_ride_events",
            )
        )

    def status(self, status: str):
        return self.filter(status=status)

    def rider_email(self, email: str):
        return self.filter(id_rider__email__iexact=email)

    def distance_from(self, latitude: float, longitude: float):
        """
        # NOTE: this uses simple Euclidean distance calculated at the database level.
        """
        return self.annotate(
            distance=Sqrt(
                Power(models.F("pickup_latitude") - latitude, 2)
                + Power(models.F("pickup_longitude") - longitude, 2)
            )
        )
