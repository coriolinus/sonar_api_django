from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User object for Sonar

    This contains user authentication data and a tiny profile.
    Per Django standards, if you expect to need complex profiles,
    it's better to use a separate table in order to reduce the size
    of the User objects used by the authentication system. However,
    for Sonar, the only profile information not already included
    in the user object is the blurb, so the increase in object size
    is compensated for by the reduction in overall system complexity.
    """
    blurb = models.CharField(
        max_length=settings.PING_LENGTH,
        blank=True,
        null=False,
        default="",
    )
