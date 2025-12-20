import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from rides.models import Ride, RideEvent, RideEventType, RideStatus
from users.models import User, UserRole


class Command(BaseCommand):
    help = "Seed the database with sample data for development"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing data before seeding",
        )
        parser.add_argument(
            "--rides",
            type=int,
            default=50,
            help="Number of rides to create (default: 50)",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            self.stdout.write("Clearing existing data...")
            RideEvent.objects.all().delete()
            Ride.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()
            self.stdout.write(self.style.SUCCESS("Cleared existing data"))

        self.stdout.write("Seeding database...")

        # Create users
        admin = self._create_or_get_user(
            username="admin",
            email="admin@wingz.com",
            first_name="Admin",
            last_name="User",
            role=UserRole.ADMIN,
            is_staff=True,
            is_superuser=True,
        )

        drivers = self._create_drivers()
        riders = self._create_riders()

        # Create rides
        num_rides = options["rides"]
        rides = self._create_rides(drivers, riders, num_rides)

        self.stdout.write(self.style.SUCCESS(f"Created {len(drivers)} drivers"))
        self.stdout.write(self.style.SUCCESS(f"Created {len(riders)} riders"))
        self.stdout.write(self.style.SUCCESS(f"Created {len(rides)} rides with events"))
        self.stdout.write(self.style.SUCCESS("Database seeding complete!"))

    def _create_or_get_user(
        self, username, email, first_name, last_name, role, **extra
    ):
        # Try to get by email first, then by username
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            pass

        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            pass

        # Create new user
        user = User.objects.create(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=role,
            phone_number=f"+1555{random.randint(1000000, 9999999)}",
            **extra,
        )
        user.set_password("password123")
        user.save()
        return user

    def _create_drivers(self):
        driver_data = [
            ("john_driver", "john.driver@wingz.com", "John", "Doe"),
            ("jane_driver", "jane.driver@wingz.com", "Jane", "Smith"),
            ("mike_driver", "mike.driver@wingz.com", "Mike", "Johnson"),
            ("sarah_driver", "sarah.driver@wingz.com", "Sarah", "Williams"),
            ("chris_driver", "chris.driver@wingz.com", "Chris", "Brown"),
        ]
        drivers = []
        for username, email, first_name, last_name in driver_data:
            driver = self._create_or_get_user(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                role=UserRole.DRIVER,
            )
            drivers.append(driver)
        return drivers

    def _create_riders(self):
        rider_data = [
            ("alice_rider", "alice.rider@example.com", "Alice", "Garcia"),
            ("bob_rider", "bob.rider@example.com", "Bob", "Martinez"),
            ("carol_rider", "carol.rider@example.com", "Carol", "Anderson"),
            ("david_rider", "david.rider@example.com", "David", "Taylor"),
            ("eve_rider", "eve.rider@example.com", "Eve", "Thomas"),
            ("frank_rider", "frank.rider@example.com", "Frank", "Jackson"),
            ("grace_rider", "grace.rider@example.com", "Grace", "White"),
            ("henry_rider", "henry.rider@example.com", "Henry", "Harris"),
        ]
        riders = []
        for username, email, first_name, last_name in rider_data:
            rider = self._create_or_get_user(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                role=UserRole.RIDER,
            )
            riders.append(rider)
        return riders

    def _create_rides(self, drivers, riders, num_rides):
        rides = []
        now = timezone.now()

        # Common locations (approximate coordinates for various cities)
        locations = [
            # San Francisco area
            (37.7749, -122.4194, 37.7849, -122.4094),
            (37.7849, -122.4094, 37.7949, -122.3994),
            (37.7649, -122.4294, 37.7549, -122.4394),
            # Los Angeles area
            (34.0522, -118.2437, 34.0622, -118.2337),
            (34.0422, -118.2537, 34.0322, -118.2637),
            # New York area
            (40.7128, -74.0060, 40.7228, -73.9960),
            (40.7028, -74.0160, 40.6928, -74.0260),
            # Chicago area
            (41.8781, -87.6298, 41.8881, -87.6198),
            # Seattle area
            (47.6062, -122.3321, 47.6162, -122.3221),
        ]

        for i in range(num_rides):
            driver = random.choice(drivers)
            rider = random.choice(riders)

            # Pick random location
            pickup_lat, pickup_lng, dropoff_lat, dropoff_lng = random.choice(locations)

            # Add some randomness to coordinates
            pickup_lat += random.uniform(-0.05, 0.05)
            pickup_lng += random.uniform(-0.05, 0.05)
            dropoff_lat += random.uniform(-0.05, 0.05)
            dropoff_lng += random.uniform(-0.05, 0.05)

            # Random pickup time within the last 30 days or next 7 days
            days_offset = random.randint(-30, 7)
            hours_offset = random.randint(0, 23)
            pickup_time = now + timedelta(days=days_offset, hours=hours_offset)

            # Determine status based on pickup time
            if pickup_time > now:
                status = RideStatus.EN_ROUTE
            elif random.random() < 0.3:
                status = RideStatus.PICKUP
            else:
                status = RideStatus.DROPOFF

            ride = Ride.objects.create(
                id_rider=rider,
                id_driver=driver,
                pickup_latitude=pickup_lat,
                pickup_longitude=pickup_lng,
                dropoff_latitude=dropoff_lat,
                dropoff_longitude=dropoff_lng,
                pickup_time=pickup_time,
                status=status,
            )

            # Create ride events based on status
            self._create_ride_events(ride, pickup_time, status)
            rides.append(ride)

        return rides

    def _create_ride_events(self, ride, pickup_time, status):
        """Create ride events for a ride based on its status."""
        events_to_create = []

        # En-route event (always created, slightly before pickup time)
        en_route_time = pickup_time - timedelta(minutes=random.randint(10, 30))
        events_to_create.append(
            RideEvent(
                id_ride=ride,
                description=RideEventType.STATUS_EN_ROUTE,
                created_at=en_route_time,
            )
        )

        if status in [RideStatus.PICKUP, RideStatus.DROPOFF]:
            # Pickup event
            actual_pickup = pickup_time + timedelta(minutes=random.randint(-5, 10))
            events_to_create.append(
                RideEvent(
                    id_ride=ride,
                    description=RideEventType.STATUS_PICKUP,
                    created_at=actual_pickup,
                )
            )

            if status == RideStatus.DROPOFF:
                # Dropoff event (ride duration between 15-90 minutes)
                ride_duration = random.randint(15, 90)
                dropoff_time = actual_pickup + timedelta(minutes=ride_duration)
                events_to_create.append(
                    RideEvent(
                        id_ride=ride,
                        description=RideEventType.STATUS_DROPOFF,
                        created_at=dropoff_time,
                    )
                )

        # Bulk create events
        RideEvent.objects.bulk_create(events_to_create)
