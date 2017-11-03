from contextlib import contextmanager
from random import choices
from string import ascii_letters, digits

from django.urls import reverse

ALPHABET = ascii_letters + digits


@contextmanager
def auth_key(client, key):
    client.credentials(HTTP_AUTHORIZATION='Token ' + key)
    yield client
    client.credentials()


class TestToolsMixin:
    def create_user(self, username='test_user', data_only=True):
        "Create a test user and return their data"
        url = reverse('user-list')
        data = {
            'username': username,
            'password': ''.join(choices(ALPHABET, k=10)),
        }
        response = self.client.post(url, data, format='json')
        if data_only:
            return response.data
        else:
            return response

    def create_ping(self, key, text='foo bar bat', data_only=True):
        url = reverse('ping-list')
        data = {'text': text}
        with auth_key(self.client, key) as auth_client:
            response = auth_client.post(url, data, format='json')
        if data_only:
            return response.data
        else:
            return response

    def create_reply(self, userkey, replied_to_data, text='i reply', data_only=True):
        reply_url = replied_to_data['url'] + 'reply/'
        with self.client_as(userkey) as auth_client:
            response = auth_client.post(
                reply_url,
                {'text': text},
                format='json',
            )
        if data_only:
            return response.data
        else:
            return response

    @contextmanager
    def client_as(self, key):
        with auth_key(self.client, key) as auth_client:
            yield auth_client

    def follow(self, follower, followee):
        with self.client_as(follower['token']) as auth_client:
            return auth_client.post(
                followee['url'] + 'follow/',
                format='json',
            )

    def unfollow(self, unfollower, unfollowee):
        with self.client_as(unfollower['token']) as auth_client:
            return auth_client.post(
                unfollowee['url'] + 'unfollow/',
                format='json',
            )
