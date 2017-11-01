from contextlib import contextmanager


@contextmanager
def auth_key(client, key):
    client.credentials(HTTP_AUTHORIZATION='Token ' + key)
    yield client
    client.credentials()
