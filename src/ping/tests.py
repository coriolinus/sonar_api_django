from datetime import timedelta
from unittest import mock

from common.testing import auth_key
from django.conf import settings
from django.urls import reverse
from django.utils.timezone import now
from ping.models import Ping
from rest_framework import status
from rest_framework.test import APITestCase


class PingTests(APITestCase):
    def create_user(self, username='test_user'):
        "Create a test user and return their API key"
        url = reverse('user-list')
        data = {
            'username': username,
            'password': 'aiouwe4nv890-',
        }
        return self.client.post(url, data, format='json').data['token']

    def create_ping(self, key, text='foo bar bat'):
        url = reverse('ping-list')
        data = {'text': text}
        with auth_key(self.client, key) as auth_client:
            return auth_client.post(url, data, format='json')

    def test_user_can_create_ping(self):
        key = self.create_user()
        text = 'foo bar bat'
        response = self.create_ping(key, text)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['text'], text)
        self.assertIs(response.data['edited'], None)
        self.assertIn('url', response.data)
        self.assertEqual(Ping.objects.count(), 1)
        ping = Ping.objects.first()
        self.assertEqual(ping.text, text)

    def test_ping_length_cannot_exceed_setting(self):
        target = settings.PING_LENGTH + 1
        text = '123456789-' * (target // 10)
        text += '123456789-'[:(target % 10)]
        self.assertEqual(len(text), target)

        key = self.create_user()
        response = self.create_ping(key, text)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Ping.objects.count(), 0)

    def test_anyone_can_see_ping(self):
        key = self.create_user()
        ping_url = self.create_ping(key).data['url']

        response = self.client.get(ping_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['text'], Ping.objects.first().text)

    def test_user_can_edit_ping(self):
        key = self.create_user()
        old_text = 'foo bar bat'
        new_text = 'bat baz bam'
        ping_data = self.create_ping(key, old_text).data

        # let's assume that there is no case in which 15 seconds will elapse
        # between creating the ping in the previous line, and editing it
        # in the subsequent line. If that anomalous case _does_ ever occur,
        # this test will break. That's your signal to run this code on a less
        # overburdened machine.

        with auth_key(self.client, key) as auth_client:
            response = auth_client.patch(
                ping_data['url'],
                {'text': new_text},
                format='json',
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['text'], new_text)
        self.assertEqual(Ping.objects.first().text, new_text)
        self.assertIs(response.data['edited'], None)

    def test_edited_shows_seconds_after_creation(self):
        current_time = now()
        one_hour_later = current_time + timedelta(hours=1)

        key = self.create_user()
        with mock.patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = current_time
            ping_data = self.create_ping(key).data

        self.assertIs(ping_data['edited'], None)

        with mock.patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = one_hour_later
            with auth_key(self.client, key) as auth_client:
                response = auth_client.patch(
                    ping_data['url'],
                    {'text': 'Greetings, from the future!'},
                    format='json',
                )

        # 3600 seconds in one hour
        self.assertEqual(response.data['edited'], 3600)

    def test_other_user_cannot_edit_ping(self):
        user1_key = self.create_user('user1')
        user2_key = self.create_user('user2')
        text = "I'm innocuous!"
        ping_data = self.create_ping(user1_key, text).data

        with auth_key(self.client, user2_key) as auth_client:
            response = auth_client.patch(
                ping_data['url'],
                {'text': 'Whoops, auth fail'},
                format='json',
            )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Ping.objects.first().text, text)

    def test_anonymous_cannot_delete_ping(self):
        key = self.create_user()
        ping_data = self.create_ping(key).data

        response = self.client.delete(ping_data['url'])
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Ping.objects.count(), 1)

    def test_ping_must_have_text(self):
        key = self.create_user()
        response = self.create_ping(key, '')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Ping.objects.count(), 0)
