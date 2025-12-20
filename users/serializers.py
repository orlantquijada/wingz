from rest_framework import serializers

from .models import User


class BaseUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id_user", "first_name", "last_name", "email", "phone_number"]
