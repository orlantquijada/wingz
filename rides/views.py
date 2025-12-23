import logging

from django.db import connection, reset_queries
from rest_framework import viewsets
from django.conf import settings

from api.permissions import IsAdminUser

from .models import Ride
from .pagination import RidePagination
from .serializers import RideSerializer, RideQueryParamsSerializer

logger = logging.getLogger(__name__)


class RideViewSet(viewsets.ModelViewSet):
    queryset = Ride.objects.all()
    serializer_class = RideSerializer
    permission_classes = [IsAdminUser]
    pagination_class = RidePagination

    def get_queryset(self):
        queryset = (
            super()
            .get_queryset()
            .with_rider_and_driver()
            .with_todays_ride_events()
            .with_pickup_event_time()
        )

        params_serializer = RideQueryParamsSerializer(data=self.request.query_params)
        params_serializer.is_valid(raise_exception=True)
        validated_data = params_serializer.validated_data

        if status := validated_data.get("status"):
            queryset = queryset.status(status)

        if rider_email := validated_data.get("rider_email"):
            queryset = queryset.rider_email(rider_email)

        if ordering := validated_data.get("ordering"):
            if ordering in ("pickup_time", "-pickup_time"):
                order_field = ordering.replace("pickup_time", "pickup_event_time")
                queryset = queryset.order_by(order_field)
            elif ordering in ("distance", "-distance"):
                latitude = validated_data.get("latitude")
                longitude = validated_data.get("longitude")

                if latitude is not None and longitude is not None:
                    queryset = queryset.distance_from(latitude, longitude).order_by(
                        ordering
                    )

        return queryset

    def list(self, request, *args, **kwargs):
        if settings.DEBUG:
            reset_queries()

        response = super().list(request, *args, **kwargs)

        if settings.DEBUG:
            logger.debug(f"{len(connection.queries)} queries")

        return response
