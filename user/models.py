# user/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class Account(AbstractUser):
    """Custom User model extending AbstractUser with additional fields."""
    bio = models.TextField(blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    last_seen = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.username
