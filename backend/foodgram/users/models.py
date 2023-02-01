from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name',)

    # USER = 'user'
    # GUEST = 'guest'
    # ADMIN = 'admin'
    # USER_ROLES = [
    #     (USER, 'user'),
    #     (GUEST, 'guest'),
    #     (ADMIN, 'admin'),
    # ]
    username = models.CharField(
        blank=False,
        max_length=150,
        unique=True,
    )
    email = models.EmailField(
        max_length=254,
        unique=True,
    )
    password = models.CharField(
        max_length=150,
        blank=True,
        null=True,
    )
    first_name = models.CharField(
        max_length=150,
        blank=True,
        null=True,
    )
    last_name = models.CharField(
        max_length=150,
        blank=True,
        null=True,
    )

    # @property
    # def is_guest(self):
    #     return self.role == self.GUEST

    # @property
    # def is_admin(self):
    #     return self.role == self.ADMIN or self.is_superuser

    # @property
    # def is_user(self):
    #     return self.role == self.USER

    class Meta:
        ordering = ('username',)

        def __str__(self):
            return self.username
