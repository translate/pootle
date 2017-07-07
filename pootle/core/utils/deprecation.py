# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.conf import settings
from django.core import checks


DEPRECATIONS = [
    # (old, new, deprecated_version, removed_version)
    # ('OLD', 'NEW', '2.7', '2.9'),
    # ('REMOVED', None, '2.7', '2.9'),
    ('TITLE', 'POOTLE_TITLE', '2.7', '2.8'),
    ('CAN_CONTACT', 'POOTLE_CONTACT_ENABLED', '2.7', '2.8'),
    ('CAN_REGISTER', 'POOTLE_SIGNUP_ENABLED', '2.7', '2.8'),
    ('CONTACT_EMAIL', 'POOTLE_CONTACT_EMAIL', '2.7', '2.8'),
    ('POOTLE_REPORT_STRING_ERRORS_EMAIL', 'POOTLE_CONTACT_REPORT_EMAIL',
     '2.7', '2.8'),
    ('PODIRECTORY', 'POOTLE_TRANSLATION_DIRECTORY', '2.7', '2.8'),
    ('MARKUP_FILTER', 'POOTLE_MARKUP_FILTER', '2.7', '2.8'),
    ('USE_CAPTCHA', 'POOTLE_CAPTCHA_ENABLED', '2.7', '2.8'),
    ('POOTLE_TOP_STATS_CACHE_TIMEOUT', None, '2.7', None),
    ('MT_BACKENDS', 'POOTLE_MT_BACKENDS', '2.7', '2.8'),
    ('ENABLE_ALT_SRC', None, '2.5', None),
    ('VCS_DIRECTORY', None, '2.7', None),
    ('CONTRIBUTORS_EXCLUDED_NAMES', None, '2.7', None),
    ('CONTRIBUTORS_EXCLUDED_PROJECT_NAMES', None, '2.7', None),
    ('MIN_AUTOTERMS', None, '2.7', None),
    ('MAX_AUTOTERMS', None, '2.7', None),
    ('DESCRIPTION', None, '2.7', None),
    ('FUZZY_MATCH_MAX_LENGTH', None, '2.7', None),
    ('FUZZY_MATCH_MIN_SIMILARITY', None, '2.7', None),
    ('OBJECT_CACHE_TIMEOUT', 'POOTLE_CACHE_TIMEOUT', '2.7', '2.8'),
    ('LEGALPAGE_NOCHECK_PREFIXES', 'POOTLE_LEGALPAGE_NOCHECK_PREFIXES',
     '2.7', '2.8'),
    ('CUSTOM_TEMPLATE_CONTEXT', 'POOTLE_CUSTOM_TEMPLATE_CONTEXT',
     '2.7', '2.8'),
    ('EXPORTED_DIRECTORY_MODE', None, '2.7', None),
    ('EXPORTED_FILE_MODE', 'POOTLE_SYNC_FILE_MODE', '2.7', '2.8'),
    ('POOTLE_SCORE_COEFFICIENTS', 'POOTLE_SCORES', '2.8', '2.8'),
]


def check_deprecated_settings(app_configs=None, **kwargs):
    errors = []

    for old, new, dep_ver, remove_ver in DEPRECATIONS:

        # Old setting just disappeared, we just want you to cleanup
        if hasattr(settings, old) and new is None:
            errors.append(checks.Info(
                ("Setting %s was removed in Pootle %s." %
                 (old, dep_ver)),
                hint=("Remove %s from your settings." % old),
                id="pootle.I002",
            ))
            continue

        # Both old and new defined, we'd like you to remove the old setting
        if hasattr(settings, old) and hasattr(settings, new):
            errors.append(checks.Info(
                ("Setting %s was replaced by %s in Pootle %s. Both are set." %
                 (old, new, dep_ver)),
                hint=("Remove %s from your settings." % old),
                id="pootle.I002",
            ))
            continue

        # Old setting is present and new setting is not defined:
        # - Warn and copy
        # - Fail hard if its too old
        if hasattr(settings, old) and not hasattr(settings, new):
            from pootle import VERSION
            if VERSION >= tuple(int(x) for x in remove_ver.split(".")):
                errors.append(checks.Critical(
                    ("Setting %s is deprecated and was removed in Pootle %s." %
                     (old, remove_ver)),
                    hint=("Use %s instead." % new),
                    id="pootle.W002",
                ))
            else:
                errors.append(checks.Warning(
                    ("Setting %s is deprecated and will be removed in "
                     "Pootle %s." % (old, remove_ver)),
                    hint=("Use %s instead." % new),
                    id="pootle.W002",
                ))
                setattr(settings, new, getattr(settings, old))
            continue

    return errors
