from rest_framework import viewsets

from api.permissions import IsAdminUser

from .models import Ride
from .serializers import RideSerializer


class RideViewSet(viewsets.ModelViewSet):
    queryset = Ride.objects.all()
    serializer_class = RideSerializer
    permission_classes = [IsAdminUser]
