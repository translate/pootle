#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import sys

from django.conf import settings


# Minimum Translate Toolkit version required for Pootle to run.
TTK_MINIMUM_REQUIRED_VERSION = (1, 11, 0)

# Minimum Django version required for Pootle to run.
DJANGO_MINIMUM_REQUIRED_VERSION = (1, 7, 7)

# Minimum lxml version required for Pootle to run.
LXML_MINIMUM_REQUIRED_VERSION = (2, 2, 2, 0)



##########################
# Test core dependencies #
##########################

def test_translate():
    try:
        from translate.__version__ import ver, sver
        if ver >= TTK_MINIMUM_REQUIRED_VERSION:
            return True, sver
        else:
            return False, sver
    except ImportError:
        return None, None


def test_django():
    from django import VERSION, get_version
    if VERSION >= DJANGO_MINIMUM_REQUIRED_VERSION:
        return True, get_version()
    else:
        return False, get_version()


def test_lxml():
    try:
        from lxml.etree import LXML_VERSION, __version__
        if LXML_VERSION >= LXML_MINIMUM_REQUIRED_VERSION:
            return True, __version__
        else:
            return False, __version__
    except ImportError:
        return None, None


def test_cache():
    """Test if cache backend is Redis."""
    if getattr(settings, "CACHES", None):
        return "RedisCache" in settings.CACHES['default']['BACKEND']


def test_cache_server_connection():
    """Test if we can connect to the cache server."""
    from django_redis import get_redis_connection
    return get_redis_connection()


##############################
# Test optional dependencies #
##############################


def test_iso_codes():
    import gettext
    languages = (lang[0] for lang in settings.LANGUAGES)
    if not languages:
        # There are no UI languages, which is a problem, but we won't complain
        # about that here.
        languages = ['af', 'ar', 'fr']
    return len(gettext.find('iso_639', languages=languages, all=True)) > 0


def test_levenshtein():
    try:
        import Levenshtein
        return True
    except ImportError:
        return False


######################
# Test optimal setup #
######################

def test_mysqldb():
    try:
        import MySQLdb
        return True
    except ImportError:
        return False


def test_db():
    """Test that we are not using sqlite3 as the django database."""
    if getattr(settings, "DATABASES", None):
        return "sqlite" not in settings.DATABASES['default']['ENGINE']


def test_session():
    """Test that session backend is set to cache or cache_db."""
    return settings.SESSION_ENGINE.split('.')[-1] in ('cache', 'cached_db')


def test_debug():
    return not settings.DEBUG


def test_webserver():
    """Test that webserver is apache."""
    return ('apache' in sys.modules or
            '_apache' in sys.modules or
            'mod_wsgi' in sys.modules)


def test_from_email():
    return bool(settings.DEFAULT_FROM_EMAIL)


def test_contact_email():
    return bool(settings.CONTACT_EMAIL)
