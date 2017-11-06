from user.models import User

from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models


class Hashtag(models.Model):
    name = models.CharField(
        max_length=settings.PING_LENGTH,
        primary_key=True,
        validators=(
            MinLengthValidator(1),
        ),
    )

    def __repr__(self):
        return f"<Hashtag: {self.name}>"

    def __str__(self):
        return f"#{self.name}"


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
    replying_to = models.ForeignKey(
        'self',
        null=True,
        default=None,
        on_delete=models.SET_NULL,
        related_name='replies',
        db_index=True,  # so that querying `ping.replies` is efficient
    )
    mentions = models.ManyToManyField(
        User,
        blank=True,
        # null has no effect on ManyToManyFields
        related_name='mentioned_by',
    )
    hashtags = models.ManyToManyField(
        Hashtag,
        blank=True,
        related_name='in_pings',
    )

    def __repr__(self):
        return "<Ping: {} @ {}>".format(self.user, self.created.isoformat())

    def save(self, *args, **kwargs):
        """
        Override the save method so that mentions and hashtags are always kept in sync
        """
        super().save(*args, **kwargs)
        self.update_content_relations()

    def update_content_relations(self):
        "Set the mentions and hashtags appropriately for this object"
        mentions = set()
        hashtags = set()
        for word in self.text.split():
            if word.startswith('@'):
                try:
                    user = User.objects.get(username=word[1:])
                except User.DoesNotExist:
                    continue
                mentions.add(user)
            elif word.startswith('#'):
                hashtag, _ = Hashtag.objects.get_or_create(name=word[1:])
                hashtags.add(hashtag)
        self.mentions.set(mentions)
        self.hashtags.set(hashtags)
