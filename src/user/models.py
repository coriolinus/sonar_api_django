from django.conf import settings
from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


class CaseInsensitiveUserManager(UserManager):
    def get_by_natural_key(self, username):
        case_insensitive_username_field = f"{self.model.USERNAME_FIELD}__iexact"
        return self.get(**{case_insensitive_username_field: username})


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

    Also, we want usernames to be case-insensitive; per a Django wart,
    by default they're case-sensitive.
    """
    objects = CaseInsensitiveUserManager()

    blurb = models.CharField(
        max_length=settings.PING_LENGTH,
        blank=True,
        null=False,
        default="",
    )


class Follow(models.Model):
    """
    Table defining which users follow which others.

    Could be implemented in terms of a generic ManyToMany on a User
    object, but the intent is more clear if we break this out as a
    first-class table.
    """
    follower = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        db_index=True,
    )
    followed = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='followed_by',
        db_index=True,
    )
    created = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        unique_together = (
            ('follower', 'followed'),
        )

    def __repr__(self):
        return f"<Follow: {self.follower} -> {self.followed}>"


class Block(models.Model):
    """
    Table defining which users block which others.

    Blocking is a _unidirectional_ relation with a _bidirectional_ effect:
    if User A blocks User B, not only does A no longer see any of B's pings,
    B is also prevented from seeing any of A's. If B then blocks A, there is no
    additional effect. If A removes the block from B, because the reverse block
    exists, nothing changes. Only when B unblocks A, so there is no longer any
    block between the two users, can they see each others' Pings again.

    Blocking is also _limited_:
    - Pings are available to the general public, so users who log out or use
      a non-logged-in anonymous session can still follow someone's timeline.
      Default-public Pings are an essential feature of the service.
    - Because of the previous point, if A requests B's timeline or a particular
      Ping of B's, they will get it, even if A has blocked B. The same is true
      in reverse.

    The following views respect blocks:
    - `/timeline/`
    - `/mentions/`
    - `/hashtags/`
    """
    blocker = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='blocks',
        db_index=True,
    )
    blocked = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='blocked_by',
        db_index=True,
    )
    created = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        unique_together = (
            ('blocker', 'blocked'),
        )

    def __repr__(self):
        return f"<Block: {self.blocker} -> {self.blocked}>"
