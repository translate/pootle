#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.core import checks
from django.utils.translation import ugettext as _


# Minimum Translate Toolkit version required for Pootle to run.
TTK_MINIMUM_REQUIRED_VERSION = (1, 11, 0)

# Minimum Django version required for Pootle to run.
DJANGO_MINIMUM_REQUIRED_VERSION = (1, 7, 8)

# Minimum lxml version required for Pootle to run.
LXML_MINIMUM_REQUIRED_VERSION = (2, 2, 2, 0)

# Minimum Redis server version required.
# Initially set to some minimums based on:
# 1. Ubuntu 12.04LTS's version 2.8.4 (10.04LTS was too old for RQ)
# 2. RQ requires >= 2.6.0, and
# 3. Wanting to insist on at least the latest stable that devs are using i.e.
#    2.8.* versions of Redis
REDIS_MINIMUM_REQUIRED_VERSION = (2, 8, 4)


# XXX List of manage.py commands not to run the rqworker check on.
# Maybe tagging can improve this?
RQWORKER_WHITELIST = [
    "start", "initdb", "revision", "sync_stores", "run_cherrypy",
    "refresh_stats", "update_stores", "calculate_checks", "retry_failed_jobs"
]


def _version_to_string(version, significance=None):
    if significance is not None:
        version = version[significance:]
    return '.'.join(str(n) for n in version)


@checks.register()
def check_library_versions(app_configs=None, **kwargs):
    from django import VERSION as django_version
    from lxml.etree import LXML_VERSION as lxml_version
    from translate.__version__ import ver as ttk_version

    errors = []

    if django_version < DJANGO_MINIMUM_REQUIRED_VERSION:
        errors.append(checks.Critical(
            _("Your version of Django is too old."),
            hint=_("Try pip install --upgrade 'Django==%s'" %
                   _version_to_string(DJANGO_MINIMUM_REQUIRED_VERSION)),
            id="pootle.C002",
        ))

    if lxml_version < LXML_MINIMUM_REQUIRED_VERSION:
        errors.append(checks.Warning(
            _("Your version of lxml is too old."),
            hint=_("Try pip install --upgrade lxml"),
            id="pootle.W003",
        ))

    if ttk_version < TTK_MINIMUM_REQUIRED_VERSION:
        errors.append(checks.Critical(
            _("Your version of Translate Toolkit is too old."),
            hint=_("Try pip install --upgrade translate-toolkit"),
            id="pootle.C003",
        ))

    return errors


@checks.register()
def check_optional_dependencies(app_configs=None, **kwargs):
    errors = []

    try:
        import Levenshtein
    except ImportError:
        errors.append(checks.Warning(
            _("Can't find python-levenshtein package. "
              "Updating against templates is faster with python-levenshtein."),
            hint=_("Try pip install python-levenshtein"),
            id="pootle.W010",
        ))

    return errors


@checks.register()
def check_redis(app_configs=None, **kwargs):
    from django_rq.queues import get_queue
    from django_rq.workers import Worker

    errors = []

    try:
        queue = get_queue()
        workers = Worker.all(queue.connection)
    except Exception as e:
        conn_settings = queue.connection.connection_pool.connection_kwargs
        errors.append(checks.Critical(_("Could not connect to Redis (%s)") % (e),
            hint=_("Make sure Redis is running on %(host)s:%(port)s") % (conn_settings),
            id="pootle.C001",
        ))
    else:
        if not workers or workers[0].stopped:
            # We need to check we're not running manage.py rqworker right now..
            import sys
            if len(sys.argv) > 1 and sys.argv[1] in RQWORKER_WHITELIST:
                errors.append(checks.Warning(
                    _("No RQ Worker running."),
                    hint=_("Run new workers with manage.py rqworker"),
                    id="pootle.W001",
                ))

        redis_version = queue.connection.info()["redis_version"].split(".")
        if tuple(int(x) for x in redis_version) < REDIS_MINIMUM_REQUIRED_VERSION:
            errors.append(checks.Warning(
                _("Your version of Redis is too old."),
                hint=_("Update your system's Redis server package"),
                id="pootle.W002",
            ))

    return errors


@checks.register()
def check_settings(app_configs=None, **kwargs):
    from django.conf import settings

    errors = []

    if "RedisCache" not in settings.CACHES.get("default", {}).get("BACKEND"):
        errors.append(checks.Critical(
            _("Cache backend is not set to Redis."),
            hint=_("Set default cache backend to django_redis.cache.RedisCache\n"
                   "Current settings: %r") % (settings.CACHES.get("default")),
            id="pootle.C005",
        ))
    else:
        from django_redis import get_redis_connection

        if not get_redis_connection():
            errors.append(checks.Critical(
                _("Could not initiate a Redis cache connection"),
                hint=_("Double-check your CACHES settings"),
                id="pootle.C004",
            ))

    if settings.DEBUG:
        errors.append(checks.Warning(
            _("DEBUG mode is on. Do not do this in production!"),
            hint=_("Set DEBUG = False in Pootle settings"),
            id="pootle.W005"
        ))
    elif "sqlite" in settings.DATABASES.get("default", {}).get("ENGINE"):
        # We don't bother warning about sqlite in DEBUG mode.
        errors.append(checks.Warning(
            _("The sqlite database backend is unsupported"),
            hint=_("Set your default database engine to postgresql_psycopg2 or mysql"),
            id="pootle.W006",
        ))

    if settings.SESSION_ENGINE.split(".")[-1] not in ("cache", "cached_db"):
        errors.append(checks.Warning(
            _("Not using cached_db as session engine"),
            hint=_("Set SESSION_ENGINE to django.contrib.sessions.backend.cached_db\n"
                   "Current settings: %r") % (settings.SESSION_ENGINE),
            id="pootle.W007",
        ))

    if not settings.CONTACT_EMAIL:
        errors.append(checks.Warning(
            _("settings.CONTACT_EMAIL is not set."),
            hint=_("Set CONTACT_EMAIL to allow users to contact administrators"
                   "through the Pootle contact form."),
            id="pootle.W008",
        ))

    if not settings.DEFAULT_FROM_EMAIL:
        errors.append(checks.Warning(
            _("settings.DEFAULT_FROM_EMAIL is not set."),
            hint=_("DEFAULT_FROM_EMAIL is used in all outgoing Pootle email.\n"
                   "Don't forget to review your mail server settings."),
            id="pootle.W009",
        ))

    return errors
