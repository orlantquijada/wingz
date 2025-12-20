# Wingz Ride API

Built with Django REST Framework, JWT authentication, and PostgreSQL.

## Quick Start

### Prerequisites

- Python 3.12+
- PostgreSQL 17
- [uv](https://github.com/astral-sh/uv) for dependency management

### Setup

1. **Start the database**:

   ```bash
   docker-compose up -d
   ```

2. **Install dependencies**:

   ```bash
   uv sync
   ```

3. **Configure environment**:

   ```bash
   cp .env.example .env
   ```

4. **Run migrations and start the server**:

   ```bash
   uv run python manage.py migrate
   uv run python manage.py runserver
   ```

5. **(Optional) Seed the database with sample data**:

   ```bash
   uv run python manage.py seed
   ```

Creates sample users, drivers, riders, and rides. Use `--clear` to reset data, or `--rides N` to specify ride count.

The API will be available at `http://localhost:8000`.

### Running Tests

```bash
uv run python manage.py test
```

---

## API Overview

### Authentication

The API uses JWT tokens. Get your tokens from:

```
POST /api/token/
{
    "username": "your_username",
    "password": "your_password"
}
```

Include the access token in requests:

```
Authorization: Bearer <access_token>
```

Refresh tokens when expired:

```
POST /api/token/refresh/
{
    "refresh": "<refresh_token>"
}
```

### Rides Endpoint

**`GET /api/rides/`** — List all rides (admin only)

Returns paginated rides with nested rider/driver info and recent events.

#### Query Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `status` | Filter by ride status | `?status=pickup` |
| `rider_email` | Filter by rider's email (case-insensitive) | `?rider_email=john@example.com` |
| `ordering` | Sort results | `?ordering=pickup_time` or `?ordering=-pickup_time` |
| `ordering` + `latitude` + `longitude` | Sort by distance from a point | `?ordering=distance&latitude=40.7128&longitude=-74.0060` |

#### Sample Response

```json
{
    "count": 42,
    "next": "http://localhost:8000/api/rides/?page=2",
    "previous": null,
    "results": [
        {
            "id_ride": 1,
            "status": "pickup",
            "rider": {
                "id_user": 2,
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com"
            },
            "driver": {
                "id_user": 3,
                "first_name": "Jane",
                "last_name": "Driver",
                "email": "jane@example.com"
            },
            "pickup_latitude": 40.7128,
            "pickup_longitude": -74.0060,
            "dropoff_latitude": 40.7580,
            "dropoff_longitude": -73.9855,
            "pickup_time": "2024-01-15T10:30:00Z",
            "todays_ride_events": [
                {
                    "id_ride_event": 5,
                    "description": "Status changed to pickup",
                    "created_at": "2024-01-15T10:32:00Z"
                }
            ]
        }
    ]
}
```

---

## Technical Decisions

### Query Performance

The ride list endpoint is optimized to run in a fixed number of queries regardless of how many rides are returned:

- `select_related` for rider and driver (avoids N+1 for user data)
- `Prefetch` with a filtered queryset for `todays_ride_events` (only fetches events from the last 24 hours, never loads the full event history)

This is tested with `assertNumQueries` to prevent accidental regressions.

### Ride Events as an Enum

I constrained the ride event descriptions to choices rather than free text. This makes querying more reliable. The trade-off is less flexibility, but being the events are well-defined, this seemed like the right call. It is still also possible to update/add on more events in the future e.g. "Driver cancelled Ride"

---

## Bonus: Trip Duration SQL Query

This query finds trips that took longer than an hour and groups them by month and driver.

### Expected Output

| Month | Driver | Count of Trips > 1 hr |
|-------|--------|----------------------|
| 2024-01 | Chris H | 4 |
| 2024-01 | Howard Y | 5 |

### The Query

```sql
WITH pickup_events AS (
    SELECT 
        id_ride,
        created_at AS pickup_time
    FROM rides_rideevent
    WHERE description = 'Status changed to pickup'
),
dropoff_events AS (
    SELECT 
        id_ride,
        created_at AS dropoff_time
    FROM rides_rideevent
    WHERE description = 'Status changed to dropoff'
),
trip_durations AS (
    SELECT 
        r.id_ride,
        r.id_driver_id AS driver_id,
        p.pickup_time,
        d.dropoff_time,
        d.dropoff_time - p.pickup_time AS duration
    FROM rides_ride r
    INNER JOIN pickup_events p ON r.id_ride = p.id_ride
    INNER JOIN dropoff_events d ON r.id_ride = d.id_ride
    WHERE d.dropoff_time > p.pickup_time
)
SELECT 
    TO_CHAR(pickup_time, 'YYYY-MM') AS "Month",
    CONCAT(u.first_name, ' ', LEFT(u.last_name, 1)) AS "Driver",
    COUNT(*) AS "Count of Trips > 1 hr"
FROM trip_durations td
INNER JOIN users_user u ON td.driver_id = u.id_user
WHERE td.duration > INTERVAL '1 hour'
GROUP BY TO_CHAR(pickup_time, 'YYYY-MM'), u.id_user, u.first_name, u.last_name
ORDER BY "Month", "Driver";
```

### How it works

1. **CTEs for pickup/dropoff events** — First two CTEs pull out the timestamps for pickup and dropoff events separately.

2. **Trip durations CTE** — Joins rides with their events to calculate how long each trip took. The `INNER JOIN` to filter out rides that don't have both events.

3. **Final aggregation** — Filters for trips over an hour, groups by month and driver, and formats the output. The driver name is formatted as "FirstName L" using `CONCAT` and `LEFT`.
