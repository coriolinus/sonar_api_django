"""
Utilities for mocking Pings
"""
from itertools import islice
from unittest import mock

from common.mock import gen_text, gen_times
from ping.models import Ping


def create_ping_at(user, text, when):
    "Utility function for mocking pings created at a specific time"
    with mock.patch('django.utils.timezone.now') as mock_now:
        mock_now.return_value = when
        return Ping.objects.create(user=user, text=text)


def gen_pings_for(user, qty, starting_at=None):
    "Generate qty random pings for user"
    for timestamp in islice(gen_times(base=starting_at), qty):
        create_ping_at(user, gen_text(), timestamp)
