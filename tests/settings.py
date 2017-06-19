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

# Ideally this setting would be set in a per-test basis, unfortunately some code
# such as `django.utils.timezone.get_default_timezone` read from this setting
# and at the same time are behind a `lru_cache` decorator, which makes it
# impossible to alter the value at runtime because decorators are applied at
# function definition time.
TIME_ZONE = 'Pacific/Honolulu'

ROOT_DIR = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
POOTLE_TRANSLATION_DIRECTORY = os.path.join(ROOT_DIR, 'pytest_pootle', 'data', 'po')


MIDDLEWARE = [
    #: Resolves paths
    'pootle.middleware.baseurl.BaseUrlMiddleware',
    #: Must be as high as possible (see above)
    'django.middleware.cache.UpdateCacheMiddleware',
    #: Avoids caching for authenticated users
    'pootle.middleware.cache.CacheAnonymousOnly',
    #: Protect against clickjacking and numerous xss attack techniques
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    #: Support for e-tag
    'django.middleware.http.ConditionalGetMiddleware',
    #: Protection against cross-site request forgery
    'django.middleware.csrf.CsrfViewMiddleware',
    #: Must be before authentication
    'django.contrib.sessions.middleware.SessionMiddleware',
    #: Must be before anything user-related
    'pootle.middleware.auth.AuthenticationMiddleware',
    #: User-related
    'django.middleware.locale.LocaleMiddleware',
    #: Nice 500 and 403 pages (must be after locale to have translated versions)
    'pootle.middleware.errorpages.ErrorPagesMiddleware',
    'django.middleware.common.CommonMiddleware',
    #: Must be early in the response cycle (close to bottom)
    'pootle.middleware.captcha.CaptchaMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

# Using the only Redis DB for testing
CACHES = {
    # Must set up entries for persistent stores here because we have a check in
    # place that will abort everything otherwise
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/13',
        'TIMEOUT': 604800,  # 1 week
    },
    'redis': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/14',
        'TIMEOUT': None,
    },
    'lru': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/15',
        'TIMEOUT': 604800,  # 1 week
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


POOTLE_EMAIL_FEEDBACK_ENABLED = True


# Faster password hasher
PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.MD5PasswordHasher',
)


SCRIPT_NAME = '/'


SILENCED_SYSTEM_CHECKS = [
    'pootle.C005',  # Silence the RedisCache check as we use a dummy cache
    'pootle.C017',  # Distinct redis DB numbers for default, redis, stats
    'pootle.W005',  # DEBUG = True
    'pootle.W011',  # POOTLE_CONTACT_EMAIL has default setting
]

try:
    if "pootle_fs" not in INSTALLED_APPS:
        INSTALLED_APPS = INSTALLED_APPS + ["pootle_fs"]
except NameError:
    INSTALLED_APPS = ["pootle_fs"]
