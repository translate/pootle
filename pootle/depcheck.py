#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009-2012 Zuza Software Foundation
# Copyright 2014-2015 Evernote Corporation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# Pootle is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# Pootle; if not, see <http://www.gnu.org/licenses/>.

import sys

from django.conf import settings


# Minimum Translate Toolkit version required for Pootle to run.
TTK_MINIMUM_REQUIRED_VERSION = (1, 11, 0)

# Minimum Django version required for Pootle to run.
DJANGO_MINIMUM_REQUIRED_VERSION = (1, 7, 4)

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


def test_redis_server_available():
    from django_rq.queues import get_queue
    from django_rq.workers import Worker
    from redis.exceptions import ConnectionError
    queue = get_queue()
    try:
        workers = Worker.all(queue.connection)
        return True, queue.connection.connection_pool.connection_kwargs
    except ConnectionError:
        return False, queue.connection.connection_pool.connection_kwargs


def test_rq_workers_running():
    from django_rq.queues import get_queue
    from django_rq.workers import Worker
    queue = get_queue()
    workers = Worker.all(queue.connection)
    return len(workers) >= 1 and not workers[0].stopped, len(workers)


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


def test_cache():
    """Test if cache backend is Redis."""
    if getattr(settings, "CACHES", None):
        return "RedisCache" in settings.CACHES['default']['BACKEND']


def test_cache_server_connection():
    """Test if we can connect to the cache server."""
    from django.core.cache import cache
    return cache._cache.servers[0].connect()


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
