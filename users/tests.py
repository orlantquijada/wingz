from rest_framework import status

from api.tests.base import BaseAPITestCase

RIDES_LIST_PATH = "/api/rides/"


class RideListAuthenticationTests(BaseAPITestCase):
    def test_anon_auth_401(self) -> None:
        response = self.client.get(RIDES_LIST_PATH)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_rider_auth_403(self) -> None:
        self._authenticate_as(self.rider_user)
        response = self.client.get(RIDES_LIST_PATH)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_driver_auth_403(self) -> None:
        self._authenticate_as(self.driver_user)
        response = self.client.get(RIDES_LIST_PATH)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_auth_200(self) -> None:
        self._authenticate_as(self.admin_user)
        response = self.client.get(RIDES_LIST_PATH)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
