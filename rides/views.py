from django.db.models import QuerySet
from rest_framework import viewsets

from api.permissions import IsAdminUser

from .models import Ride
from .serializers import RideSerializer, RideQueryParamsSerializer


class RideViewSet(viewsets.ModelViewSet):
    queryset = Ride.objects.all()
    serializer_class = RideSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self) -> QuerySet:
        queryset = super().get_queryset()

        params_serializer = RideQueryParamsSerializer(data=self.request.query_params)
        params_serializer.is_valid(raise_exception=True)
        validated_data = params_serializer.validated_data

        if status := validated_data.get("status"):
            queryset = queryset.status(status)

        if rider_email := validated_data.get("rider_email"):
            queryset = queryset.rider_email(rider_email)

        if ordering := validated_data.get("ordering"):
            if ordering in ("pickup_time", "-pickup_time"):
                queryset = queryset.order_by(ordering)

        return queryset
