from datetime import timedelta
from unittest import mock

from common.testing import TestToolsMixin
from django.conf import settings
from django.utils.timezone import now
from ping.models import Ping
from rest_framework import status
from rest_framework.test import APITestCase


class PingTests(TestToolsMixin, APITestCase):

    def test_user_can_create_ping(self):
        key = self.create_user()['token']
        text = 'foo bar bat'
        response = self.create_ping(key, text, data_only=False)
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

        key = self.create_user()['token']
        response = self.create_ping(key, text, data_only=False)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Ping.objects.count(), 0)

    def test_anyone_can_see_ping(self):
        key = self.create_user()['token']
        ping_url = self.create_ping(key)['url']

        response = self.client.get(ping_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['text'], Ping.objects.first().text)

    def test_user_can_edit_ping(self):
        key = self.create_user()['token']
        old_text = 'foo bar bat'
        new_text = 'bat baz bam'
        ping_data = self.create_ping(key, old_text)

        # let's assume that there is no case in which 15 seconds will elapse
        # between creating the ping in the previous line, and editing it
        # in the subsequent line. If that anomalous case _does_ ever occur,
        # this test will break. That's your signal to run this code on a less
        # overburdened machine.

        with self.client_as(key) as auth_client:
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

        key = self.create_user()['token']
        with mock.patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = current_time
            ping_data = self.create_ping(key)

        self.assertIs(ping_data['edited'], None)

        with mock.patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = one_hour_later
            with self.client_as(key) as auth_client:
                response = auth_client.patch(
                    ping_data['url'],
                    {'text': 'Greetings, from the future!'},
                    format='json',
                )

        # 3600 seconds in one hour
        self.assertEqual(response.data['edited'], 3600)

    def test_other_user_cannot_edit_ping(self):
        user1_key = self.create_user('user1')['token']
        user2_key = self.create_user('user2')['token']
        text = "I'm innocuous!"
        ping_data = self.create_ping(user1_key, text)

        with self.client_as(user2_key) as auth_client:
            response = auth_client.patch(
                ping_data['url'],
                {'text': 'Whoops, auth fail'},
                format='json',
            )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Ping.objects.first().text, text)

    def test_anonymous_cannot_delete_ping(self):
        key = self.create_user()['token']
        ping_data = self.create_ping(key)

        response = self.client.delete(ping_data['url'])
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Ping.objects.count(), 1)

    def test_ping_must_have_text(self):
        key = self.create_user()['token']
        response = self.create_ping(key, '', data_only=False)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Ping.objects.count(), 0)

    def test_users_can_reply_to_pings(self):
        user1key = self.create_user('user1')['token']
        ping1data = self.create_ping(user1key)

        user2key = self.create_user('user2')['token']
        with self.client_as(user2key) as auth_client:
            reply_url = ping1data['url'] + 'reply/'
            response = auth_client.post(
                reply_url,
                {'text': 'responding to a prior ping'},
                format='json',
            )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNot(response.data['replying_to'], None)

    def test_ping_multiple_replies(self):
        "Ensure that we can fetch multiple replies for a single ping"
        user1 = self.create_user('user1')['token']
        user2 = self.create_user('user2')['token']
        user3 = self.create_user('user3')['token']

        p1 = self.create_ping(user1)
        p2 = self.create_reply(user2, p1)
        p3 = self.create_reply(user2, p1, 'another from me on this topic')
        p4 = self.create_reply(user3, p1)

        replies_urls = {result['url']
                        for result
                        in self.client.get(p1['url'] + 'replies/').data['results']}

        for ping in (p2, p3, p4):
            self.assertIn(ping['url'], replies_urls)

    def test_reply_chain(self):
        "Pings can reply to each other in arbitrary chains"
        user_root = self.create_user('root')['token']
        user_left = self.create_user('left')['token']
        user_right = self.create_user('right')['token']

        root_ping = self.create_ping(user_root, 'root ping')
        left_1 = self.create_reply(user_left, root_ping, 'left 1')
        right_1 = self.create_reply(user_right, root_ping, 'right 1')
        left_2 = self.create_reply(user_left, right_1, 'left 2')
        right_2 = self.create_reply(user_right, right_1, 'right 2')

        for expect_replied_to, expect_replies in (
            (root_ping, [left_1, right_1]),
            (left_1, []),
            (right_1, [left_2, right_2]),
            (left_2, []),
            (right_2, []),
        ):
            replies_urls = {
                result['url']
                for result
                in self.client.get(
                    expect_replied_to['url'] + 'replies/'
                ).data['results']
            }

            for ping in expect_replies:
                self.assertIn(ping['url'], replies_urls)
