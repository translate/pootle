#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Test settings."""

import os

SECRET_KEY = "test_secret_key"


ROOT_DIR = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
PODIRECTORY = os.path.join(ROOT_DIR, 'tests', 'data', 'po')


# In-memory caching
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'pootle-tests'
    }
}


# Mail server settings
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


# Faster password hasher
PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.MD5PasswordHasher',
)
