from rest_framework import serializers

from users.models import User
from users.serializers import BaseUserSerializer

from .models import Ride, RideEvent, RideStatus


class RideQueryParamsSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=RideStatus.choices,
        required=False,
    )
    rider_email = serializers.EmailField(
        required=False,
    )

    ORDERING_CHOICES = [
        ("pickup_time", "Ascending by pickup time"),
        ("-pickup_time", "Descending by pickup time"),
        ("distance", "Ascending by distance from coordinates"),
        ("-distance", "Descending by distance from coordinates"),
    ]
    ordering = serializers.ChoiceField(
        choices=ORDERING_CHOICES,
        required=False,
        help_text="Sort rides by pickup_time or distance",
    )

    latitude = serializers.FloatField(
        required=False,
        min_value=-90,
        max_value=90,
    )
    longitude = serializers.FloatField(
        required=False,
        min_value=-180,
        max_value=180,
    )

    def validate(self, attrs):
        ordering = attrs.get("ordering")
        if ordering in ("distance", "-distance"):
            if "latitude" not in attrs or "longitude" not in attrs:
                raise serializers.ValidationError(
                    "latitude and longitude are required when ordering by distance"
                )
        return attrs


class RideEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = RideEvent
        fields = ["id_ride_event", "description", "created_at"]


class RideSerializer(serializers.ModelSerializer):
    rider = BaseUserSerializer(source="id_rider", read_only=True)
    driver = BaseUserSerializer(source="id_driver", read_only=True)

    rider_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="id_rider", write_only=True
    )
    driver_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="id_driver", write_only=True
    )

    todays_ride_events = RideEventSerializer(many=True, read_only=True)

    class Meta:
        model = Ride
        fields = [
            "id_ride",
            "status",
            "rider",
            "driver",
            "rider_id",
            "driver_id",
            "pickup_latitude",
            "pickup_longitude",
            "dropoff_latitude",
            "dropoff_longitude",
            "pickup_time",
            "todays_ride_events",
        ]
