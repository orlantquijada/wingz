from typing import Self

from django.db import models
from django.db.models.functions import Power, Sqrt


class RideQuerySet(models.QuerySet):
    def status(self, status: str):
        return self.filter(status=status)

    def rider_email(self, email: str):
        return self.filter(id_rider__email__iexact=email)

    def distance_from(self, latitude: float, longitude: float) -> Self:
        """
        # NOTE: this uses simple Euclidean distance calculated at the database level.
        """
        return self.annotate(
            distance=Sqrt(
                Power(models.F("pickup_latitude") - latitude, 2)
                + Power(models.F("pickup_longitude") - longitude, 2)
            )
        )
