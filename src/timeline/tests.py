from time import sleep

from common.testing import TestToolsMixin
from rest_framework import status
from rest_framework.test import APITestCase
from timeline.views import TimelineViewSet

# strictly speaking, it's possible to use other page sizes
# elsewhere in the app, but practically speaking, I'm keeping
# things consistent
PAGE_SIZE = TimelineViewSet.pagination_class.page_size


class UserTimelineTests(TestToolsMixin, APITestCase):
    def test_user_timeline_works(self):
        user = self.create_user()
        ping1 = self.create_ping(user['token'], 'ping1')
        ping2 = self.create_ping(user['token'], 'ping2')

        with self.client_as(user['token']) as auth_client:
            tl_resp = auth_client.get('/timeline/')
        self.assertEqual(tl_resp.status_code, status.HTTP_200_OK)

        self.assertEqual(
            {ping['url'] for ping in tl_resp.data['results']},
            {ping1['url'], ping2['url']}
        )

    def test_user_timeline_is_ordered_desc(self):
        user = self.create_user()
        ping1 = self.create_ping(user['token'], 'ping1')
        ping2 = self.create_ping(user['token'], 'ping2')

        self.assertEqual(
            [ping['url'] for ping in
             self.client.get(user['url'] + 'timeline/').data['results']],
            [ping['url'] for ping in (ping2, ping1)]
        )

    def test_user_timeline_is_paginated(self):
        user = self.create_user()
        for _ in range(PAGE_SIZE + 1):
            self.create_ping(user['token'])

        tl_data = self.client.get(user['url'] + 'timeline/').data
        self.assertEqual(len(tl_data['results']), PAGE_SIZE)
        self.assertIsNot(tl_data['next'], None)

    def test_user_timeline_includes_no_other_users(self):
        user1 = self.create_user('user1')
        self.create_ping(user1['token'])
        self.create_ping(user1['token'])

        user2 = self.create_user('user2')
        ping = self.create_ping(user2['token'])

        tl_data = self.client.get(user2['url'] + 'timeline/').data
        self.assertEqual(len(tl_data['results']), 1)
        self.assertEqual(tl_data['results'][0]['url'], ping['url'])


class TimelineTests(TestToolsMixin, APITestCase):
    def test_timeline_works(self):
        user = self.create_user()
        ping1 = self.create_ping(user['token'], 'ping1')
        ping2 = self.create_ping(user['token'], 'ping2')

        with self.client_as(user['token']) as auth_client:
            tl_resp = auth_client.get('/timeline/')
        self.assertEqual(tl_resp.status_code, status.HTTP_200_OK)

        self.assertEqual(
            {ping['url'] for ping in tl_resp.data['results']},
            {ping1['url'], ping2['url']}
        )

    def test_timeline_is_ordered_desc(self):
        user1 = self.create_user('user1')
        user2 = self.create_user('user2')

        self.follow(user1, user2)

        ping1 = self.create_ping(user1['token'], 'ping1')
        ping2 = self.create_ping(user2['token'], 'ping2')

        with self.client_as(user1['token']) as auth_client:
            tl_resp = auth_client.get('/timeline/')
        self.assertEqual(tl_resp.status_code, status.HTTP_200_OK)

        self.assertEqual(
            [ping['url'] for ping in tl_resp.data['results']],
            [ping['url'] for ping in (ping2, ping1)]
        )

    def test_timeline_is_paginated(self):
        user = self.create_user()
        for _ in range(PAGE_SIZE + 1):
            self.create_ping(user['token'])

        with self.client_as(user['token']) as auth_client:
            tl_resp = auth_client.get('/timeline/')
        self.assertEqual(tl_resp.status_code, status.HTTP_200_OK)

        self.assertEqual(len(tl_resp.data['results']), PAGE_SIZE)
        self.assertIsNot(tl_resp.data['next'], None)

    def test_timeline_interleaves_multiple_users(self):
        user1 = self.create_user('user1')
        user2 = self.create_user('user2')
        user3 = self.create_user('user3')
        self.follow(user1, user2)
        self.follow(user1, user3)

        created_pings = []

        for idx in range(2):
            for user in (user1, user2, user3):
                created_pings.append(
                    self.create_ping(user['token'], f"{user['username']} interleave with {idx}")
                )
                sleep(0.01)

        with self.client_as(user1['token']) as auth_client:
            tl_resp = auth_client.get('/timeline/')
        self.assertEqual(tl_resp.status_code, status.HTTP_200_OK)

        self.assertEqual(
            [res['url'] for res in tl_resp.data['results']],
            [p['url'] for p in reversed(created_pings)]
        )

    def test_timeline_includes_only_followed_users(self):
        user1 = self.create_user('user1')
        user2 = self.create_user('user2')
        user3 = self.create_user('user3')
        self.follow(user1, user2)

        for idx in range(2):
            for user in (user1, user2, user3):
                self.create_ping(user['token'], f"{user['username']} interleave with {idx}")
                sleep(0.01)

        with self.client_as(user1['token']) as auth_client:
            tl_resp = auth_client.get('/timeline/')
        self.assertEqual(tl_resp.status_code, status.HTTP_200_OK)

        self.assertEqual(len(tl_resp.data['results']), 4)
        for ping in tl_resp.data['results']:
            self.assertNotEqual(ping['user'], user3['url'])
