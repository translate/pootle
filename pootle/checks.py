# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import sys

from django.core import checks
from django.db import OperationalError, ProgrammingError

from pootle.constants import DJANGO_MINIMUM_REQUIRED_VERSION
from pootle.i18n.gettext import ugettext as _


# Minimum Translate Toolkit version required for Pootle to run.
TTK_MINIMUM_REQUIRED_VERSION = (2, 2, 5)

# Minimum lxml version required for Pootle to run.
LXML_MINIMUM_REQUIRED_VERSION = (3, 5, 0, 0)

# Minimum Redis server version required.
# Initially set to some minimums based on:
# 1. Ubuntu 16.04LTS (Xenial) version 3.0.6
#    Ubuntu 14.04LTS (Trusty) version 2.8.4
#    Ubuntu 12.04LTS (Precise) version 2.2.12
#    Ubuntu 10.04LTS was too old for RQ
#    See http://packages.ubuntu.com/search?keywords=redis-server
# 2. RQ requires Redis >= 2.7.0, and
#    See https://github.com/nvie/rq/blob/master/README.md
# 3. django-redis 4.x.y supports Redis >=2.8.x
#    See http://niwinz.github.io/django-redis/latest/
# 4. Aligning with current Redis stable as best we can
#    At the time of writing, actual Redis stable is 3.0 series with 2.8
#    cosidered old stable.
# 5. Wanting to insist on at least the latest stable that devs are using
#    The 2.8.* versions of Redis
REDIS_MINIMUM_REQUIRED_VERSION = (2, 8, 4)


# List of pootle commands that need a running rqworker.
# FIXME Maybe tagging can improve this?
RQWORKER_WHITELIST = [
    "revision", "retry_failed_jobs", "check", "runserver",
]

EXPECTED_POOTLE_SCORES = [
    'suggestion_add',
    'suggestion_accept',
    'suggestion_reject',
    'comment_updated',
    'target_updated',
    'state_translated',
    'state_fuzzy',
    'state_unfuzzy']


def _version_to_string(version, significance=None):
    if significance is not None:
        version = version[significance:]
    return '.'.join(str(n) for n in version)


@checks.register('data')
def check_duplicate_emails(app_configs=None, **kwargs):
    from accounts.utils import get_duplicate_emails
    errors = []
    try:
        if len(get_duplicate_emails()):
            errors.append(
                checks.Warning(
                    _("There are user accounts with duplicate emails. This "
                      "will not be allowed in Pootle 2.8."),
                    hint=_("Try using 'pootle find_duplicate_emails', and "
                           "then update user emails with 'pootle "
                           "update_user_email username email'. You might also "
                           "want to consider using pootle merge_user or "
                           "purge_user commands"),
                    id="pootle.W017"
                )
            )
    except (OperationalError, ProgrammingError):
        # no accounts set up - most likely in a test
        pass
    return errors


@checks.register()
def check_library_versions(app_configs=None, **kwargs):
    from django import VERSION as DJANGO_VERSION
    from lxml.etree import LXML_VERSION
    from translate.__version__ import ver as ttk_version

    errors = []

    if DJANGO_VERSION < DJANGO_MINIMUM_REQUIRED_VERSION:
        errors.append(checks.Critical(
            _("Your version of Django is too old."),
            hint=_("Try pip install --upgrade 'Django==%s'",
                   _version_to_string(DJANGO_MINIMUM_REQUIRED_VERSION)),
            id="pootle.C002",
        ))

    if LXML_VERSION < LXML_MINIMUM_REQUIRED_VERSION:
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
def check_redis(app_configs=None, **kwargs):
    from django_rq.queues import get_queue
    from django_rq.workers import Worker

    errors = []

    try:
        queue = get_queue()
        Worker.all(queue.connection)
    except Exception as e:
        conn_settings = queue.connection.connection_pool.connection_kwargs
        errors.append(checks.Critical(
            _("Could not connect to Redis (%s)", e),
            hint=_("Make sure Redis is running on "
                   "%(host)s:%(port)s") % conn_settings,
            id="pootle.C001",
        ))
    else:
        redis_version = tuple(int(x) for x
                              in (queue.connection
                                       .info()["redis_version"].split(".")))
        if redis_version < REDIS_MINIMUM_REQUIRED_VERSION:
            errors.append(checks.Critical(
                _("Your version of Redis is too old."),
                hint=_("Update your system's Redis server package to at least "
                       "version %s", str(REDIS_MINIMUM_REQUIRED_VERSION)),
                id="pootle.C007",
            ))

        if len(queue.connection.smembers(Worker.redis_workers_keys)) == 0:
            # If we're not running 'pootle rqworker' report for whitelisted
            # commands
            if len(sys.argv) > 1 and sys.argv[1] in RQWORKER_WHITELIST:
                errors.append(checks.Warning(
                    # Translators: a worker processes background tasks
                    _("No worker running."),
                    # Translators: a worker processes background tasks
                    hint=_("Run new workers with 'pootle rqworker'"),
                    id="pootle.W001",
                ))

    return errors


@checks.register()
def check_settings(app_configs=None, **kwargs):
    from django.conf import settings

    errors = []

    if "RedisCache" not in settings.CACHES.get("default", {}).get("BACKEND"):
        errors.append(checks.Critical(
            _("Cache backend is not set to Redis."),
            hint=_("Set default cache backend to "
                   "django_redis.cache.RedisCache\n"
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

    redis_cache_aliases = ("default", "redis", "lru")
    redis_locations = set()
    for alias in redis_cache_aliases:
        if alias in settings.CACHES:
            redis_locations.add(settings.CACHES.get(alias, {}).get("LOCATION"))

    if len(redis_locations) < len(redis_cache_aliases):
        errors.append(checks.Critical(
            _("Distinct django_redis.cache.RedisCache configurations "
              "are required for `default`, `redis` and `lru`."),
            hint=_("Double-check your CACHES settings"),
            id="pootle.C017",
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
            hint=_("Set your default database engine to postgresql "
                   "or mysql"),
            id="pootle.W006",
        ))

    if settings.SESSION_ENGINE.split(".")[-1] not in ("cache", "cached_db"):
        errors.append(checks.Warning(
            _("Not using cached_db as session engine"),
            hint=_("Set SESSION_ENGINE to "
                   "django.contrib.sessions.backend.cached_db\n"
                   "Current settings: %r") % (settings.SESSION_ENGINE),
            id="pootle.W007",
        ))

    if not settings.POOTLE_CONTACT_EMAIL and settings.POOTLE_CONTACT_ENABLED:
        errors.append(checks.Warning(
            _("POOTLE_CONTACT_EMAIL is not set."),
            hint=_("Set POOTLE_CONTACT_EMAIL to allow users to contact "
                   "administrators through the Pootle contact form."),
            id="pootle.W008",
        ))

    if settings.POOTLE_CONTACT_EMAIL in ("info@YOUR_DOMAIN.com") \
       and settings.POOTLE_CONTACT_ENABLED:
        errors.append(checks.Warning(
            _("POOTLE_CONTACT_EMAIL is using the following default "
              "setting %r." % settings.POOTLE_CONTACT_EMAIL),
            hint=_("POOTLE_CONTACT_EMAIL is the address that will receive "
                   "messages sent by the contact form."),
            id="pootle.W011",
        ))

    if not settings.DEFAULT_FROM_EMAIL:
        errors.append(checks.Warning(
            _("DEFAULT_FROM_EMAIL is not set."),
            hint=_("DEFAULT_FROM_EMAIL is used in all outgoing Pootle email.\n"
                   "Don't forget to review your mail server settings."),
            id="pootle.W009",
        ))

    if settings.DEFAULT_FROM_EMAIL in ("info@YOUR_DOMAIN.com",
                                       "webmaster@localhost"):
        errors.append(checks.Warning(
            _("DEFAULT_FROM_EMAIL is using the following default "
              "setting %r." % settings.DEFAULT_FROM_EMAIL),
            hint=_("DEFAULT_FROM_EMAIL is used in all outgoing Pootle email.\n"
                   "Don't forget to review your mail server settings."),
            id="pootle.W010",
        ))

    if settings.POOTLE_TM_SERVER:
        tm_indexes = []

        for server in settings.POOTLE_TM_SERVER:
            if 'INDEX_NAME' not in settings.POOTLE_TM_SERVER[server]:
                errors.append(checks.Critical(
                    _("POOTLE_TM_SERVER['%s'] has no INDEX_NAME.", server),
                    hint=_("Set an INDEX_NAME for POOTLE_TM_SERVER['%s'].",
                           server),
                    id="pootle.C008",
                ))
            elif settings.POOTLE_TM_SERVER[server]['INDEX_NAME'] in tm_indexes:
                errors.append(checks.Critical(
                    _("Duplicate '%s' INDEX_NAME in POOTLE_TM_SERVER.",
                      settings.POOTLE_TM_SERVER[server]['INDEX_NAME']),
                    hint=_("Set different INDEX_NAME for all servers in "
                           "POOTLE_TM_SERVER."),
                    id="pootle.C009",
                ))
            else:
                tm_indexes.append(
                    settings.POOTLE_TM_SERVER[server]['INDEX_NAME'])

            if 'ENGINE' not in settings.POOTLE_TM_SERVER[server]:
                errors.append(checks.Critical(
                    _("POOTLE_TM_SERVER['%s'] has no ENGINE.", server),
                    hint=_("Set a ENGINE for POOTLE_TM_SERVER['%s'].",
                           server),
                    id="pootle.C010",
                ))

            if 'HOST' not in settings.POOTLE_TM_SERVER[server]:
                errors.append(checks.Critical(
                    _("POOTLE_TM_SERVER['%s'] has no HOST.", server),
                    hint=_("Set a HOST for POOTLE_TM_SERVER['%s'].",
                           server),
                    id="pootle.C011",
                ))

            if 'PORT' not in settings.POOTLE_TM_SERVER[server]:
                errors.append(checks.Critical(
                    _("POOTLE_TM_SERVER['%s'] has no PORT.", server),
                    hint=_("Set a PORT for POOTLE_TM_SERVER['%s'].",
                           server),
                    id="pootle.C012",
                ))

            if ('WEIGHT' in settings.POOTLE_TM_SERVER[server] and
                not (0.0 <= settings.POOTLE_TM_SERVER[server]['WEIGHT']
                     <= 1.0)):
                errors.append(checks.Warning(
                    _("POOTLE_TM_SERVER['%s'] has a WEIGHT less than 0.0 or "
                      "greater than 1.0", server),
                    hint=_("Set a WEIGHT between 0.0 and 1.0 (both included) "
                           "for POOTLE_TM_SERVER['%s'].", server),
                    id="pootle.W019",
                ))

    for coefficient_name in EXPECTED_POOTLE_SCORES:
        if coefficient_name not in settings.POOTLE_SCORES:
            errors.append(checks.Critical(
                _("POOTLE_SCORES has no %s.", coefficient_name),
                hint=_("Set %s in POOTLE_SCORES.",
                       coefficient_name),
                id="pootle.C014",
            ))
        else:
            coef = settings.POOTLE_SCORES[coefficient_name]
            if not isinstance(coef, (float, int)):
                errors.append(checks.Critical(
                    _("Invalid value for %s in POOTLE_SCORES.",
                      coefficient_name),
                    hint=_(
                        "Set a valid value for %s "
                        "in POOTLE_SCORES.", coefficient_name),
                    id="pootle.C015"))
    return errors


@checks.register()
def check_settings_markup(app_configs=None, **kwargs):
    from django.conf import settings

    errors = []

    try:
        markup_filter = settings.POOTLE_MARKUP_FILTER[0]
    except AttributeError:
        errors.append(checks.Warning(
            _("POOTLE_MARKUP_FILTER is missing."),
            hint=_("Set POOTLE_MARKUP_FILTER."),
            id="pootle.W012",
        ))
    except (IndexError, TypeError, ValueError):
        errors.append(checks.Warning(
            _("Invalid value in POOTLE_MARKUP_FILTER."),
            hint=_("Set a valid value for POOTLE_MARKUP_FILTER."),
            id="pootle.W013",
        ))
    else:
        if markup_filter is not None:
            try:
                if markup_filter == 'textile':
                    import textile  # noqa
                elif markup_filter == 'markdown':
                    import markdown  # noqa
                elif markup_filter == 'restructuredtext':
                    import docutils  # noqa
                elif markup_filter == 'html':
                    pass
                else:
                    errors.append(checks.Warning(
                        _("Invalid markup in POOTLE_MARKUP_FILTER."),
                        hint=_("Set a valid markup for POOTLE_MARKUP_FILTER."),
                        id="pootle.W014",
                    ))
            except ImportError:
                errors.append(checks.Warning(
                    _("POOTLE_MARKUP_FILTER is set to '%s' markup, but the "
                      "package that provides can't be found.", markup_filter),
                    hint=_("Install the package or change "
                           "POOTLE_MARKUP_FILTER."),
                    id="pootle.W015",
                ))
        if markup_filter is None:
            errors.append(checks.Warning(
                _("POOTLE_MARKUP_FILTER set to 'None' is deprecated."),
                hint=_("Set your markup to 'html' explicitly."),
                id="pootle.W025",
            ))
        if markup_filter in ('html', 'textile', 'restructuredtext'):
            errors.append(checks.Warning(
                _("POOTLE_MARKUP_FILTER is using '%s' markup, which is "
                  "deprecated and will be removed in future.",
                  markup_filter),
                hint=_("Convert your staticpages to Markdown and set your "
                       "markup to 'markdown'."),
                id="pootle.W026",
            ))
    return errors


@checks.register('data')
def check_users(app_configs=None, **kwargs):
    from django.contrib.auth import get_user_model

    errors = []

    User = get_user_model()
    try:
        admin_user = User.objects.get(username='admin')
    except (User.DoesNotExist, OperationalError, ProgrammingError):
        pass
    else:
        if admin_user.check_password('admin'):
            errors.append(checks.Warning(
                _("The default 'admin' user still has a password set to "
                  "'admin'."),
                hint=_("Remove the 'admin' user or change its password."),
                id="pootle.W016",
            ))

    return errors


@checks.register()
def check_db_transaction_hooks(app_configs=None, **kwargs):
    from django.conf import settings

    errors = []
    if settings.DATABASES['default']['ENGINE'].startswith("transaction_hooks"):
        errors.append(checks.Critical(
            _("Database connection uses transaction_hooks."),
            hint=_("Set the DATABASES['default']['ENGINE'] to use a Django "
                   "backend from django.db.backends."),
            id="pootle.C006",
        ))
    return errors


@checks.register()
def check_email_server_is_alive(app_configs=None, **kwargs):
    from django.conf import settings

    errors = []
    if settings.POOTLE_SIGNUP_ENABLED or settings.POOTLE_CONTACT_ENABLED:
        from django.core.mail import get_connection

        connection = get_connection()
        try:
            connection.open()
        except Exception:
            errors.append(checks.Warning(
                _("Email server is not available."),
                hint=_("Review your email settings and make sure your email "
                       "server is working."),
                id="pootle.W004",
            ))
        else:
            connection.close()
    return errors


@checks.register('data')
def check_revision(app_configs=None, **kwargs):
    from redis.exceptions import ConnectionError

    from pootle.core.models import Revision
    from pootle_store.models import Unit

    errors = []
    try:
        revision = Revision.get()
    except (ConnectionError):
        return errors
    try:
        max_revision = Unit.max_revision()
    except (OperationalError, ProgrammingError):
        return errors
    if revision is None or revision < max_revision:
        errors.append(checks.Critical(
            _("Revision is missing or has an incorrect value."),
            hint=_("Run `revision --restore` to reset the revision counter."),
            id="pootle.C016",
        ))

    return errors


@checks.register()
def check_canonical_url(app_configs=None, **kwargs):
    from django.conf import settings
    from django.contrib.sites.models import Site

    errors = []
    no_canonical_error = checks.Critical(
        _("No canonical URL provided and default site set to example.com."),
        hint=_(
            "Set the `POOTLE_CANONICAL_URL` in settings or update the "
            "default site if you are using django.contrib.sites."),
        id="pootle.C018")
    localhost_canonical_warning = checks.Warning(
        _("Canonical URL is set to http://localhost."),
        hint=_(
            "Set the `POOTLE_CANONICAL_URL` to an appropriate value for your "
            "site or leave it empty if you are using `django.contrib.sites`."),
        id="pootle.W020")
    try:
        contrib_site = Site.objects.get_current()
    except (ProgrammingError, OperationalError):
        if "django.contrib.sites" in settings.INSTALLED_APPS:
            return []
        contrib_site = None
    uses_sites = (
        not settings.POOTLE_CANONICAL_URL
        and contrib_site)
    if uses_sites:
        site = Site.objects.get_current()
        if site.domain == "example.com":
            errors.append(no_canonical_error)
    elif not settings.POOTLE_CANONICAL_URL:
        errors.append(no_canonical_error)
    elif settings.POOTLE_CANONICAL_URL == "http://localhost":
        errors.append(localhost_canonical_warning)
    return errors


@checks.register()
def check_pootle_fs_working_dir(app_configs=None, **kwargs):
    import os

    from django.conf import settings

    missing_setting_error = checks.Critical(
        _("POOTLE_FS_WORKING_PATH setting is not set."),
        id="pootle.C019",
    )
    missing_directory_error = checks.Critical(
        _("Path ('%s') pointed to by POOTLE_FS_WORKING_PATH doesn't exist."
          % settings.POOTLE_FS_WORKING_PATH),
        hint=_("Create the directory pointed to by `POOTLE_FS_WORKING_PATH`, "
               "or change the setting."),
        id="pootle.C020",
    )
    not_writable_directory_error = checks.Critical(
        _("Path ('%s') pointed to by POOTLE_FS_WORKING_PATH is not writable by "
          "Pootle."
          % settings.POOTLE_FS_WORKING_PATH),
        hint=_("Add the write permission to the `POOTLE_FS_WORKING_PATH` "
               "or change the setting."),
        id="pootle.C021",
    )
    errors = []
    if not settings.POOTLE_FS_WORKING_PATH:
        errors.append(missing_setting_error)
    elif not os.path.exists(settings.POOTLE_FS_WORKING_PATH):
        errors.append(missing_directory_error)
    elif not os.access(settings.POOTLE_FS_WORKING_PATH, os.W_OK):
        errors.append(not_writable_directory_error)
    return errors


@checks.register()
def check_mysql_timezones(app_configs=None, **kwargs):
    from django.db import connection

    missing_mysql_timezone_tables = checks.Critical(
        _("MySQL requires time zone settings."),
        hint=("Load the time zone tables "
              "http://dev.mysql.com/doc/refman/5.7/en/mysql-tzinfo-to-sql.html"),
        id="pootle.C022",
    )
    errors = []
    with connection.cursor() as cursor:
        if hasattr(cursor.db, "mysql_version"):
            cursor.execute("SELECT CONVERT_TZ(NOW(), 'UTC', 'UTC');")
            converted_now = cursor.fetchone()[0]
            if converted_now is None:
                errors.append(missing_mysql_timezone_tables)
    return errors


@checks.register()
def check_unsupported_python(app_configs=None, **kwargs):
    errors = []
    if sys.version_info >= (3, 0):
        errors.append(checks.Critical(
            _("Pootle does not yet support Python 3."),
            hint=_("Use a Python 2.7 virtualenv."),
            id="pootle.C023",
        ))
    if sys.version_info < (2, 7):
        errors.append(checks.Critical(
            _("Pootle no longer supports Python versions older than 2.7"),
            hint=_("Use a Python 2.7 virtualenv."),
            id="pootle.C024",
        ))
    return errors
