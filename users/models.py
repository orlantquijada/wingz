from django.contrib.auth.models import AbstractUser
from django.db import models


class UserRole(models.TextChoices):
    ADMIN = "admin", "Admin"
    DRIVER = "driver", "Driver"
    RIDER = "rider", "Rider"


class User(AbstractUser):
    id_user = models.AutoField(primary_key=True)

    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.RIDER,
        db_index=True,
    )
    phone_number = models.CharField(max_length=20, blank=True)

    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"
