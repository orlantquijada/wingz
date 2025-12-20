from datetime import timedelta

from django.utils import timezone
from rest_framework import status

from api.tests.base import BaseAPITestCase
from rides.models import Ride, RideEvent, RideEventType, RideStatus

RIDES_LIST_PATH = "/api/rides/"


class RideListPaginationTests(BaseAPITestCase):
    def test_pagination_exists(self):
        """Test that response is paginated."""
        self._authenticate_as(self.admin_user)
        response = self.client.get(RIDES_LIST_PATH)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)


class RideListFilteringTests(BaseAPITestCase):
    @classmethod
    def setUpTestData(cls):
        """Rides with different statuses and riders."""
        super().setUpTestData()
        cls.ride_enroute = Ride.objects.create(
            status=RideStatus.EN_ROUTE,
            id_rider=cls.rider_user,
            id_driver=cls.driver_user,
            pickup_latitude=40.7128,
            pickup_longitude=-74.0060,
            dropoff_latitude=40.7580,
            dropoff_longitude=-73.9855,
            pickup_time=timezone.now(),
        )
        cls.ride_pickup = Ride.objects.create(
            status=RideStatus.PICKUP,
            id_rider=cls.rider_user,
            id_driver=cls.driver_user,
            pickup_latitude=40.7128,
            pickup_longitude=-74.0060,
            dropoff_latitude=40.7580,
            dropoff_longitude=-73.9855,
            pickup_time=timezone.now(),
        )
        cls.ride_dropoff = Ride.objects.create(
            status=RideStatus.DROPOFF,
            id_rider=cls.rider_user_2,  # Different rider
            id_driver=cls.driver_user,
            pickup_latitude=40.7128,
            pickup_longitude=-74.0060,
            dropoff_latitude=40.7580,
            dropoff_longitude=-73.9855,
            pickup_time=timezone.now(),
        )

    def test_filter_by_status(self):
        self._authenticate_as(self.admin_user)

        test_cases = [
            ("pickup", 1, self.ride_pickup.id_ride),
            ("en-route", 1, self.ride_enroute.id_ride),
        ]

        for status_val, expected_count, expected_ride_id in test_cases:
            with self.subTest(status=status_val):
                response = self.client.get(f"{RIDES_LIST_PATH}?status={status_val}")

                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response.data["count"], expected_count)
                self.assertEqual(
                    response.data["results"][0]["id_ride"], expected_ride_id
                )

    def test_filter_by_rider_email(self):
        self._authenticate_as(self.admin_user)
        response = self.client.get(f"{RIDES_LIST_PATH}?rider_email=rider@example.com")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return 2 rides (en-route and pickup belong to rider@example.com)
        self.assertEqual(response.data["count"], 2)

    def test_combined_filters(self):
        """status and rider_email filters"""
        self._authenticate_as(self.admin_user)
        response = self.client.get(
            f"{RIDES_LIST_PATH}?status=en-route&rider_email=rider@example.com"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)


class RideListSortingTests(BaseAPITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        now = timezone.now()

        # earliest pickup, farthest from reference point
        cls.ride_early_far = Ride.objects.create(
            status=RideStatus.EN_ROUTE,
            id_rider=cls.rider_user,
            id_driver=cls.driver_user,
            pickup_latitude=41.0,
            pickup_longitude=-74.0,
            dropoff_latitude=40.7580,
            dropoff_longitude=-73.9855,
            pickup_time=now - timedelta(hours=2),
        )
        # middle pickup, middle distance
        cls.ride_middle = Ride.objects.create(
            status=RideStatus.EN_ROUTE,
            id_rider=cls.rider_user,
            id_driver=cls.driver_user,
            pickup_latitude=40.75,
            pickup_longitude=-74.0,
            dropoff_latitude=40.7580,
            dropoff_longitude=-73.9855,
            pickup_time=now - timedelta(hours=1),
        )
        # latest pickup, closest to reference point
        cls.ride_late_close = Ride.objects.create(
            status=RideStatus.EN_ROUTE,
            id_rider=cls.rider_user,
            id_driver=cls.driver_user,
            pickup_latitude=40.71,
            pickup_longitude=-74.0,
            dropoff_latitude=40.7580,
            dropoff_longitude=-73.9855,
            pickup_time=now,
        )

    def test_sort_by_pickup_time_ascending(self):
        self._authenticate_as(self.admin_user)
        response = self.client.get(f"{RIDES_LIST_PATH}?ordering=pickup_time")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]

        # Should be ordered: early -> middle -> late
        self.assertEqual(results[0]["id_ride"], self.ride_early_far.id_ride)
        self.assertEqual(results[1]["id_ride"], self.ride_middle.id_ride)
        self.assertEqual(results[2]["id_ride"], self.ride_late_close.id_ride)

    def test_sort_by_distance(self):
        """Sorting by distance to a given GPS position."""
        self._authenticate_as(self.admin_user)
        # Reference point: 40.7128, -74.0060 (NYC)
        response = self.client.get(
            f"{RIDES_LIST_PATH}?ordering=distance&latitude=40.7128&longitude=-74.0060"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]

        # Should be ordered by proximity: close -> middle -> far
        self.assertEqual(results[0]["id_ride"], self.ride_late_close.id_ride)
        self.assertEqual(results[1]["id_ride"], self.ride_middle.id_ride)
        self.assertEqual(results[2]["id_ride"], self.ride_early_far.id_ride)


class RideListPerformanceTests(BaseAPITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        now = timezone.now()

        # Create multiple rides
        cls.rides = []
        for i in range(5):
            ride = Ride.objects.create(
                status=RideStatus.EN_ROUTE,
                id_rider=cls.rider_user,
                id_driver=cls.driver_user,
                pickup_latitude=40.7128,
                pickup_longitude=-74.0060,
                dropoff_latitude=40.7580,
                dropoff_longitude=-73.9855,
                pickup_time=now + timedelta(hours=i),
            )
            cls.rides.append(ride)

            recent_event = RideEvent.objects.create(
                id_ride=ride,
                description=RideEventType.STATUS_PICKUP,
            )

            old_event = RideEvent.objects.create(
                id_ride=ride,
                description=RideEventType.STATUS_EN_ROUTE,
            )
            # Manually update to 25 hours ago
            RideEvent.objects.filter(pk=old_event.pk).update(
                created_at=now - timedelta(hours=25)
            )

    def test_query_count_optimized(self):
        """
        Expected queries:
        1. Rides with select_related for rider + driver
        2. Today's RideEvents via prefetch_related
        3. Pagination count (optional)
        """
        self._authenticate_as(self.admin_user)

        with self.assertNumQueries(3):
            response = self.client.get(RIDES_LIST_PATH)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_todays_ride_events_only_recent(self):
        """
        Test that todays_ride_events only includes events from last 24h.
        """
        self._authenticate_as(self.admin_user)
        response = self.client.get(RIDES_LIST_PATH)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        for ride_data in response.data["results"]:
            todays_events = ride_data.get("todays_ride_events", [])
            # Each ride should only have 1 recent event (the pickup one)
            # The old en-route event should be excluded
            self.assertEqual(len(todays_events), 1)
            self.assertEqual(
                todays_events[0]["description"], RideEventType.STATUS_PICKUP
            )

    def test_no_n_plus_one_queries(self):
        self._authenticate_as(self.admin_user)

        with self.assertNumQueries(3):
            response = self.client.get(RIDES_LIST_PATH)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            # Access nested data to ensure no lazy loading occurs
            for ride in response.data["results"]:
                _ = ride.get("id_rider")
                _ = ride.get("id_driver")
                _ = ride.get("todays_ride_events")


class RideListResponseStructureTests(BaseAPITestCase):
    """
    - Tests response includes nested rider and driver objects
    - Tests response includes todays_ride_events
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.ride = Ride.objects.create(
            status=RideStatus.EN_ROUTE,
            id_rider=cls.rider_user,
            id_driver=cls.driver_user,
            pickup_latitude=40.7128,
            pickup_longitude=-74.0060,
            dropoff_latitude=40.7580,
            dropoff_longitude=-73.9855,
            pickup_time=timezone.now(),
        )
        cls.event = RideEvent.objects.create(
            id_ride=cls.ride,
            description=RideEventType.STATUS_EN_ROUTE,
        )

    def test_response_includes_nested_rider(self):
        self._authenticate_as(self.admin_user)
        response = self.client.get(RIDES_LIST_PATH)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ride = response.data["results"][0]

        self.assertIn("id_rider", ride)
        rider = ride["id_rider"]
        self.assertIn("email", rider)
        self.assertEqual(rider["email"], "rider@example.com")

    def test_response_includes_nested_driver(self):
        self._authenticate_as(self.admin_user)
        response = self.client.get(RIDES_LIST_PATH)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ride = response.data["results"][0]

        self.assertIn("id_driver", ride)
        driver = ride["id_driver"]
        self.assertIn("email", driver)
        self.assertEqual(driver["email"], "driver@example.com")

    def test_response_includes_todays_ride_events(self):
        self._authenticate_as(self.admin_user)
        response = self.client.get(RIDES_LIST_PATH)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ride = response.data["results"][0]

        self.assertIn("todays_ride_events", ride)
        self.assertIsInstance(ride["todays_ride_events"], list)
        self.assertEqual(len(ride["todays_ride_events"]), 1)
