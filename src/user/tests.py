from user.models import Follows, User

from common.testing import auth_key
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase


class UserTests(APITestCase):
    def create_user(self, data):
        url = reverse('user-list')
        return self.client.post(url, data, format='json')

    def test_create_user(self):
        response = self.create_user({
            'username': 'test_user',
            'password': 'test_user_pw',
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.first().username, 'test_user')
        self.assertIn('token', response.data)

    def test_username_conflict(self):
        self.create_user({
            'username': 'test_user',
            'password': 'test_user_pw',
        })
        response = self.create_user({
            'username': 'test_user',
            'password': 'test_user_pw',
        })
        self.assertNotEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)

    def test_create_user_needs_username(self):
        response = self.create_user({
            'password': 'test_user_pw',
        })
        self.assertNotEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 0)

    def test_create_user_needs_password(self):
        response = self.create_user({
            'username': 'test_user',
        })
        self.assertNotEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 0)

    def test_token_not_in_non_create_responses(self):
        response = self.create_user({
            'username': 'test_user',
            'password': 'test_user_pw',
        })
        url = response.data['url']
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('token', response.data)

    def test_user_modification_requires_token(self):
        response = self.create_user({
            'username': 'test_user',
            'password': 'test_user_pw',
        })

        token = response.data['token']
        url = response.data['url']

        patch_data = {'blurb': 'some test blurb'}

        # try patching this user without credentials
        response = self.client.patch(url,
                                     patch_data,
                                     format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # now use the correct credentials
        token = Token.objects.get(user__username='test_user')
        with auth_key(self.client, token.key) as auth_client:
            response = auth_client.patch(url,
                                         patch_data,
                                         format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for key in patch_data.keys():
            self.assertEqual(response.data[key], patch_data[key])

    def test_username_cannot_be_changed(self):
        response = self.create_user({
            'username': 'test_user',
            'password': 'test_user_pw',
        })
        url = response.data['url']

        token = Token.objects.get(user__username='test_user')
        with auth_key(self.client, token.key) as auth_client:
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
        response = self.create_user({
            'username': 'test_user_1',
            'password': 'test_user_1_pw',
        })

        user1url = response.data['url']

        response = self.create_user({
            'username': 'test_user_2',
            'password': 'test_user_2_pw',
        })
        user2token = response.data['token']

        patch_data = {'blurb': 'b;alwkerjfaklsweuhj'}

        with auth_key(self.client, user2token) as auth_client:
            response = auth_client.patch(user1url, patch_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(User.objects.get(username='test_user_1').blurb, '')

    def create_user_simple(self, username):
        return self.create_user({'username': username, 'password': 'awfuiois'})

    def follow(self, follower, followee):
        with auth_key(self.client, follower['token']) as auth_client:
            return auth_client.post(
                followee['url'] + 'follow/',
                format='json',
            )

    def unfollow(self, unfollower, unfollowee):
        with auth_key(self.client, unfollower['token']) as auth_client:
            return auth_client.post(
                unfollowee['url'] + 'unfollow/',
                format='json',
            )

    def following_urls(self, as_user):
        with auth_key(self.client, as_user['token']) as auth_client:
            return {
                result['url'] for result
                in auth_client.get('/users/following/').data['results']
            }

    def followed_by_urls(self, as_user):
        with auth_key(self.client, as_user['token']) as auth_client:
            return {
                result['url'] for result
                in auth_client.get('/users/followed-by/').data['results']
            }

    def test_user_can_follow_another(self):
        user1 = self.create_user_simple('user1').data
        user2 = self.create_user_simple('user2').data

        self.assertEqual(
            Follows.objects.filter(follower__username='user1',
                                   followed__username='user2').count(),
            0
        )
        self.assertEqual(
            Follows.objects.filter(follower__username='user2',
                                   followed__username='user1').count(),
            0
        )
        follow_resp = self.follow(user1, user2)
        self.assertEqual(follow_resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            Follows.objects.filter(follower__username='user1',
                                   followed__username='user2').count(),
            1
        )
        self.assertEqual(
            Follows.objects.filter(follower__username='user2',
                                   followed__username='user1').count(),
            0
        )
        follow_resp = self.follow(user1, user2)
        self.assertEqual(follow_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(
            Follows.objects.filter(follower__username='user1',
                                   followed__username='user2').count(),
            1
        )
        self.assertEqual(
            Follows.objects.filter(follower__username='user2',
                                   followed__username='user1').count(),
            0
        )

    def test_follow_stats(self):
        user1 = self.create_user_simple('user1').data

        stats = self.client.get(user1['url'] + 'follow-stats/').data
        self.assertEqual(stats['following'], 0)
        self.assertEqual(stats['followed'], 0)

        user2 = self.create_user_simple('user2').data
        self.follow(user1, user2)

        stats = self.client.get(user1['url'] + 'follow-stats/').data
        self.assertEqual(stats['following'], 1)
        self.assertEqual(stats['followed'], 0)

        stats = self.client.get(user2['url'] + 'follow-stats/').data
        self.assertEqual(stats['following'], 0)
        self.assertEqual(stats['followed'], 1)

    def test_user_cannot_follow_self(self):
        user = self.create_user_simple('user').data
        follow_resp = self.follow(user, user)
        self.assertEqual(follow_resp.status_code, status.HTTP_400_BAD_REQUEST)

        stats = self.client.get(user['url'] + 'follow-stats/').data
        self.assertEqual(stats['following'], 0)
        self.assertEqual(stats['followed'], 0)

    def test_user_can_unfollow_another(self):
        user1 = self.create_user_simple('user1').data
        user2 = self.create_user_simple('user2').data

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
        user1 = self.create_user_simple('user1').data
        user2 = self.create_user_simple('user2').data

        unfollow_resp = self.unfollow(user1, user2)
        self.assertEqual(unfollow_resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_user_cannot_unfollow_self(self):
        user1 = self.create_user_simple('user1').data

        unfollow_resp = self.unfollow(user1, user1)
        self.assertEqual(unfollow_resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_following_view(self):
        user1 = self.create_user_simple('user1').data
        user2 = self.create_user_simple('user2').data
        user3 = self.create_user_simple('user3').data

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
        user1 = self.create_user_simple('user1').data
        user2 = self.create_user_simple('user2').data
        user3 = self.create_user_simple('user3').data

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
