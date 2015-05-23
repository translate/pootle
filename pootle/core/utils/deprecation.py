#!/usr/bin/env python
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
            if VERSION >= tuple([int(x) for x in remove_ver.split(".")]):
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
