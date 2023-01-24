from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    USER = 'user'
    GUEST = 'guest'
    ADMIN = 'admin'
    USER_ROLES = [
        (USER, 'user'),
        (GUEST, 'guest'),
        (ADMIN, 'admin'),
    ]
    email = models.EmailField(
        max_length=254,
        unique=True,
    )
    password = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )
    first_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )
    last_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )

    @property
    def is_admin(self):
        return self.role == self.ADMIN or self.is_superuser

    @property
    def is_user(self):
        return self.role == self.USER

    class Meta:
        ordering = ('username',)

        def __str__(self):
            return self.username
