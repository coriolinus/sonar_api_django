from user.models import User

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
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = self.client.patch(url,
                                     patch_data,
                                     format='json')
        self.client.credentials()

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
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

        response = self.client.patch(
            url,
            {
                'username': 'not_the_test_user'
            },
            format='json',
        )

        self.client.credentials()

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

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + user2token)
        response = self.client.patch(user1url, patch_data, format='json')
        self.client.credentials()

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(User.objects.get(username='test_user_1').blurb, '')
