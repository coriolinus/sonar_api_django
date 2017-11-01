from user.models import User

from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models

# Create your models here.


class Ping(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='pings',
        db_index=True,
    )
    created = models.DateTimeField(auto_now_add=True, db_index=True)
    edited = models.DateTimeField(auto_now=True)
    text = models.CharField(
        max_length=settings.PING_LENGTH,
        blank=False,
        null=False,
        validators=(
            MinLengthValidator(1),
        ),
    )

    def __repr__(self):
        return "<Ping: {} @ {}>".format(self.user, self.created.isoformat())
