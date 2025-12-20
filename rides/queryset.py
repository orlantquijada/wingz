from typing import Self

from django.db import models
from django.db.models.functions import ACos, Cos, Radians, Sin
from django.http import QueryDict


class RideQuerySet(models.QuerySet):
    def status(self, status: str):
        return self.filter(status=status)

    def rider_email(self, email: str):
        return self.filter(id_rider__email__iexact=email)
