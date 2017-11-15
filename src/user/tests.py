from user.models import Follow, User

from common.testing import TestToolsMixin
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class UserTests(TestToolsMixin, APITestCase):
    def test_create_user(self):
        response = self.create_user(data_only=False)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.first().username, 'test_user')
        self.assertIn('token', response.data)

    def test_username_conflict(self):
        self.create_user()
        response = self.create_user(data_only=False)
        self.assertNotEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)

    def test_create_user_needs_username(self):
        url = reverse('user-list')
        data = {
            'password': 'test_user_pw',
        }
        response = self.client.post(url, data, format='json')
        self.assertNotEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 0)

    def test_create_user_needs_password(self):
        url = reverse('user-list')
        data = {
            'username': 'test_user',
        }
        response = self.client.post(url, data, format='json')
        self.assertNotEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 0)

    def test_token_not_in_non_create_responses(self):
        url = self.create_user()['url']
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('token', response.data)

    def test_user_modification_requires_token(self):
        user = self.create_user()
        url = user['url']

        patch_data = {'blurb': 'some test blurb'}

        # try patching this user without credentials
        response = self.client.patch(url,
                                     patch_data,
                                     format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # now use the correct credentials
        with self.client_as(user['token']) as auth_client:
            response = auth_client.patch(url,
                                         patch_data,
                                         format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for key in patch_data.keys():
            self.assertEqual(response.data[key], patch_data[key])

    def test_username_cannot_be_changed(self):
        user = self.create_user()
        url = user['url']

        with self.client_as(user['token']) as auth_client:
            response = auth_client.patch(
                url,
                {
                    'username': 'not_the_test_user'
                },
                format='json',
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.first().username, 'test_user')
        self.assertIn('username', response.data)
        self.assertEqual(response.data['username'], 'test_user')

    def test_users_cannot_modify_each_other(self):
        user1url = self.create_user('test_user_1')['url']

        user2token = self.create_user('test_user_2')['token']

        patch_data = {'blurb': 'b;alwkerjfaklsweuhj'}

        with self.client_as(user2token) as auth_client:
            response = auth_client.patch(user1url, patch_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(User.objects.get(username='test_user_1').blurb, '')

    def following_urls(self, as_user):
        with self.client_as(as_user['token']) as auth_client:
            return {
                result['url'] for result
                in auth_client.get('/users/following/').data['results']
            }

    def followed_by_urls(self, as_user):
        with self.client_as(as_user['token']) as auth_client:
            return {
                result['url'] for result
                in auth_client.get('/users/followed-by/').data['results']
            }

    def test_user_can_follow_another(self):
        user1 = self.create_user('user1')
        user2 = self.create_user('user2')

        self.assertEqual(
            Follow.objects.filter(follower__username='user1',
                                   followed__username='user2').count(),
            0
        )
        self.assertEqual(
            Follow.objects.filter(follower__username='user2',
                                   followed__username='user1').count(),
            0
        )
        follow_resp = self.follow(user1, user2)
        self.assertEqual(follow_resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            Follow.objects.filter(follower__username='user1',
                                   followed__username='user2').count(),
            1
        )
        self.assertEqual(
            Follow.objects.filter(follower__username='user2',
                                   followed__username='user1').count(),
            0
        )
        follow_resp = self.follow(user1, user2)
        self.assertEqual(follow_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(
            Follow.objects.filter(follower__username='user1',
                                   followed__username='user2').count(),
            1
        )
        self.assertEqual(
            Follow.objects.filter(follower__username='user2',
                                   followed__username='user1').count(),
            0
        )

    def test_follow_stats(self):
        user1 = self.create_user('user1')

        stats = self.client.get(user1['url'] + 'follow-stats/').data
        self.assertEqual(stats['following'], 0)
        self.assertEqual(stats['followed'], 0)

        user2 = self.create_user('user2')
        self.follow(user1, user2)

        stats = self.client.get(user1['url'] + 'follow-stats/').data
        self.assertEqual(stats['following'], 1)
        self.assertEqual(stats['followed'], 0)

        stats = self.client.get(user2['url'] + 'follow-stats/').data
        self.assertEqual(stats['following'], 0)
        self.assertEqual(stats['followed'], 1)

    def test_user_cannot_follow_self(self):
        user = self.create_user('user')
        follow_resp = self.follow(user, user)
        self.assertEqual(follow_resp.status_code, status.HTTP_400_BAD_REQUEST)

        stats = self.client.get(user['url'] + 'follow-stats/').data
        self.assertEqual(stats['following'], 0)
        self.assertEqual(stats['followed'], 0)

    def test_user_can_unfollow_another(self):
        user1 = self.create_user('user1')
        user2 = self.create_user('user2')

        self.follow(user1, user2)
        unfollow_resp = self.unfollow(user1, user2)
        self.assertEqual(unfollow_resp.status_code, status.HTTP_204_NO_CONTENT)

        stats = self.client.get(user1['url'] + 'follow-stats/').data
        self.assertEqual(stats['following'], 0)
        self.assertEqual(stats['followed'], 0)

        stats = self.client.get(user2['url'] + 'follow-stats/').data
        self.assertEqual(stats['following'], 0)
        self.assertEqual(stats['followed'], 0)

    def test_unfollow_not_already_followed(self):
        user1 = self.create_user('user1')
        user2 = self.create_user('user2')

        unfollow_resp = self.unfollow(user1, user2)
        self.assertEqual(unfollow_resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_user_cannot_unfollow_self(self):
        user1 = self.create_user('user1')

        unfollow_resp = self.unfollow(user1, user1)
        self.assertEqual(unfollow_resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_following_view(self):
        user1 = self.create_user('user1')
        user2 = self.create_user('user2')
        user3 = self.create_user('user3')

        # user1 follows user2 but _not_ user3
        # user2 follows user3 and user1
        # user3 follows only user1
        for follower, followees in (
            (user1, [user2]),
            (user2, [user3, user1]),
            (user3, [user1])
        ):
            # set up fixture
            for followee in followees:
                self.follow(follower, followee)

            # ensure that the right people show up in the following view
            following_urls = self.following_urls(follower)
            for followee in followees:
                self.assertEqual({f['url'] for f in followees}, following_urls)

    def test_followed_by_view(self):
        user1 = self.create_user('user1')
        user2 = self.create_user('user2')
        user3 = self.create_user('user3')

        # user1 follows user2 but _not_ user3
        # user2 follows user3 and user1
        # user3 follows only user1
        for follower, followees in (
            (user1, [user2]),
            (user2, [user3, user1]),
            (user3, [user1])
        ):
            # set up fixture
            for followee in followees:
                self.follow(follower, followee)

        # therefore:
        # user1 is followed by user2 and user3
        # user2 is followed by user1
        # user3 is followed by user2
        for followed, followers in (
            (user1, [user2, user3]),
            (user2, [user1]),
            (user3, [user2]),
        ):
            follower_urls = self.followed_by_urls(followed)
            self.assertEqual({f['url'] for f in followers}, follower_urls)
