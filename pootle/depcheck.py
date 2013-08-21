#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009-2012 Zuza Software Foundation
# Copyright 2014 Evernote Corporation
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

import os
import subprocess
import sys

from django.conf import settings


# Minimum Translate Toolkit version required for Pootle to run.
TTK_MINIMUM_REQUIRED_VERSION = (1, 12, 0)

# Minimum Django version required for Pootle to run.
DJANGO_MINIMUM_REQUIRED_VERSION = (1, 6, 5)

# Minimum lxml version required for Pootle to run.
LXML_MINIMUM_REQUIRED_VERSION = (2, 3, 6, 0)


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


##############################
# Test optional dependencies #
##############################

def test_unzip():
    """Test for unzip command."""
    try:
        subprocess.call('unzip', stdout=file(os.devnull),
                        stderr=file(os.devnull))
        return True
    except:
        return False


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


def test_indexer():
    from translate.search.indexing import _get_available_indexers
    return [indexer.__module__.split('.')[-1]
            for indexer in _get_available_indexers()]


def test_gaupol():
    try:
        import aeidon
        return True
    except ImportError:
        try:
            import gaupol
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
    else:
        return getattr(settings, "DATABASE_ENGINE", None) != 'sqlite3'


def test_cache():
    """Test if cache backend is memcached."""
    #FIXME: maybe we shouldn't complain if cache is set to db or file?
    if getattr(settings, "CACHES", None):
        return "memcache" in settings.CACHES['default']['BACKEND']
    else:
        return settings.CACHE_BACKEND.startswith('memcached')


def test_memcache():
    try:
        import memcache
        return True
    except ImportError:
        try:
            import pylibmc
            return True
        except ImportError:
            return False


def test_memcached():
    """Test if we can connect to memcache server."""
    from django.core.cache import cache
    return cache._cache.servers[0].connect()


def test_session():
    """Test that session backend is set to memcache."""
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
