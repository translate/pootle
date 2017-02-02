

from django.contrib.auth import get_user_model


def get_system_user():
    return get_user_model().objects.get_system_user()


def get_system_user_id():
    return get_system_user().id
