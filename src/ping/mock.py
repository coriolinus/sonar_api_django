"""
Utilities for mocking Pings
"""
from datetime import timedelta
from itertools import islice
from random import choices, randint
from unittest import mock

from django.conf import settings
from django.utils.timezone import now
from ping.models import Ping


def create_ping_at(user, text, when):
    "Utility function for mocking pings created at a specific time"
    with mock.patch('django.utils.timezone.now') as mock_now:
        mock_now.return_value = when
        return Ping.objects.create(user=user, text=text)


def gen_times(base=None, seconds_min=60, seconds_max=3600):
    """
    Generator which produces an increasing sequence of times.

    - `base` is the first value which should be returned. If `None`,
        it returns the current time
    - `seconds_min` is the minimum number of seconds before the
        next time which should be returned
    - `seconds_max` is the maximum number of seconds before the next time
        which should be returned
    """
    if base is None:
        base = now()
    while True:
        yield base
        base += timedelta(seconds=randint(seconds_min, seconds_max))


# these are the unique words from jabberwocky
WORDLIST = [
    'time', 'so', 'sword', 'awhile', 'came', 'outgrabe', 'burbled', 'the', 'bird', 'claws',
    'took', 'tulgey', 'frabjous', 'he', 'callay', 'two', 'long', '--', 'wabe', 'in', 'mome',
    'manxome', 'were', 'left', 'shun', 'jaws', 'catch', 'mimsy', 'hand', 'and', 'of',
    'callooh', 'thought', 'gimble', 'to', 'wood', 'as', 'brillig', 'vorpal', 'tree', 'flame',
    'back', 'dead', 'rested', 'joy', 'has', 'beamish', 'whiffling', 'arms', 'my', 'his',
    'all', 'went', 'come', 'beware', 'did', 'toves', 'sought', 'tumtum', 'frumious', 'stood',
    'that', 'chortled', 'its', 'through', 'galumphing', 'day', 'jabberwock', 'foe', 'boy',
    'raths', 'bandersnatch', 'o', 'borogoves', 'slain', 'jubjub', 'twas', 'thou', 'one',
    'slithy', 'blade', 'it', 'bite', 'by', 'head', 'with', 'son', 'gyre', 'snicker-snack',
    'eyes', 'uffish'
]
try:
    with open('/usr/share/dict/words') as word_file:
        WORDLIST.extend((word.strip() for word in word_file.readlines()))
except Exception:
    # we don't care what the problem is; we have a good default
    pass


def gen_text():
    text = ' '.join(choices(WORDLIST, k=randint(1, 50)))
    if len(text) > settings.PING_LENGTH:
        last_space = text.rfind(' ', 0, settings.PING_LENGTH)
        if last_space == -1:
            # couldn't find a space, so just truncate
            text = text[:settings.PING_LENGTH]
        else:
            text = text[:last_space]
    return text


def gen_pings_for(user, qty):
    "Generate qty random pings for user"
    for timestamp in islice(gen_times(), qty):
        create_ping_at(user, gen_text(), timestamp)
