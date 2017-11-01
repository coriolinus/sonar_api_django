from datetime import timedelta
from itertools import islice
from random import choice, randint, sample
from unittest import mock
from user.models import Follows, User

from common.mock import WORDLIST, gen_text, gen_times
from django.db import IntegrityError
from ping.mock import gen_pings_for
from ping.models import Ping


def create_user_at(when):
    """
    Create a random user

    This user has no password and cannot be logged in as.
    """
    username = "'"
    while "'" in username:
        username = choice(WORDLIST).lower()

    data = {
        'username': username,
    }
    if bool(randint(0, 1)):
        data['first_name'] = choice(WORDLIST)
    if bool(randint(0, 1)):
        data['last_name'] = choice(WORDLIST)
    if bool(randint(0, 1)):
        data['blurb'] = gen_text()

    try:
        with mock.patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = when
            return User.objects.create_user(**data)
    except IntegrityError:
        return None  # no problem; try again


def create_users(qty):
    for timestamp in islice(gen_times(forwards=False,
                                      min_interval=timedelta(hours=2),
                                      max_interval=timedelta(days=2)),
                            qty):
        user = create_user_at(timestamp)
        if user:
            print(f"created user: {user.username}")
            # create some pings for them
            gen_pings_for(user,
                          randint(5, 100),
                          starting_at=timestamp)
            print("  ... and {} pings".format(
                Ping.objects.filter(user=user).count()
            ))


def generate_follows(target_qty, clear_first=True):
    if clear_first:
        Follows.objects.delete()
    else:
        target_qty += Follows.objects.count()
    all_users = list(User.objects.all())
    while Follows.objects.count() < target_qty:
        origin, recipient = sample(all_users, 2)
        Follows.objects.get_or_create(follower=origin, followed=recipient)


def populate(qty, clear_first=True, follows_per_user=16):
    if clear_first:
        User.objects.delete()
    create_users(qty)
    print("generating follows...")
    generate_follows(qty * follows_per_user, clear_first)
