#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

"""Test settings."""

import os


SECRET_KEY = "test_secret_key"


ROOT_DIR = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
POOTLE_TRANSLATION_DIRECTORY = os.path.join(ROOT_DIR, 'pytest_pootle', 'data', 'po')


# Using the only Redis DB for testing
CACHES = {
    # Must set up entries for persistent stores here because we have a check in
    # place that will abort everything otherwise
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/15',
        'TIMEOUT': None,
    },
    'redis': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/15',
        'TIMEOUT': None,
    },
    'stats': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/15',
        'TIMEOUT': None,
    },
    'exports': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': os.path.join(ROOT_DIR, 'tests', 'exports'),
        'TIMEOUT': 259200,  # 3 days.
    },
}

# Using synchronous mode for testing
RQ_QUEUES = {
    'default': {
        'USE_REDIS_CACHE': 'redis',
        'DEFAULT_TIMEOUT': 360,
        'ASYNC': False,
    },
}

# Mail server settings
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


# Faster password hasher
PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.MD5PasswordHasher',
)


SILENCED_SYSTEM_CHECKS = [
    'pootle.C005',  # Silence the RedisCache check as we use a dummy cache
    'pootle.C017',  # Distinct redis DB numbers for default, redis, stats
    'pootle.W005',  # DEBUG = True
    'pootle.W011',  # POOTLE_CONTACT_EMAIL has default setting
]
