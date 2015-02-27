#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL2
# license. See the LICENSE file for a copy of the license and the AUTHORS file
# for copyright and authorship information.

"""Test settings."""

import os

SECRET_KEY = "test_secret_key"


ROOT_DIR = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
PODIRECTORY = os.path.join(ROOT_DIR, 'tests', 'data', 'po')


# Dummy caching
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'pootle-tests'
    },
    # Must set up entries for persistent stores here because we have a
    # check in place that will abort everything otherwise
    'redis': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'TIMEOUT': None,
    },
    'stats': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'TIMEOUT': None,
    },
}


# Mail server settings
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


# Faster password hasher
PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.MD5PasswordHasher',
)
