from django.urls import reverse
from rest_framework.test import APITestCase

from users.models import User, UserRole


class BaseAPITestCase(APITestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.admin_user = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            first_name="Admin",
            last_name="User",
            role=UserRole.ADMIN,
            password="testpass123",
        )
        cls.rider_user = User.objects.create_user(
            username="rider",
            email="rider@example.com",
            first_name="John",
            last_name="Rider",
            role=UserRole.RIDER,
            password="testpass123",
        )
        cls.rider_user_2 = User.objects.create_user(
            username="rider2",
            email="jane@example.com",
            first_name="Jane",
            last_name="Doe",
            role=UserRole.RIDER,
            password="testpass123",
        )
        cls.driver_user = User.objects.create_user(
            username="driver",
            email="driver@example.com",
            first_name="Test",
            last_name="Driver",
            role=UserRole.DRIVER,
            password="testpass123",
        )

    def _get_tokens(self, user: User) -> dict:
        response = self.client.post(
            reverse("token_obtain_pair"),
            {"username": user.username, "password": "testpass123"},
            format="json",
        )
        return response.data

    def _authenticate_as(self, user: User):
        tokens = self._get_tokens(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
