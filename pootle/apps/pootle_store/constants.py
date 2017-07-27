# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle.i18n.gettext import ugettext_lazy as _


#: Mapping of allowed sorting criteria.
#: Keys are supported query strings, values are the field + order that
#: will be used against the DB.
ALLOWED_SORTS = {
    'units': {
        'priority': '-store__priority',
        'oldest': 'change__submitted_on',
        'newest': '-change__submitted_on',
    },
    'suggestions': {
        'oldest': 'suggestion__creation_time',
        'newest': '-suggestion__creation_time',
    },
    'submissions': {
        'oldest': 'submission__creation_time',
        'newest': '-submission__creation_time',
    },
}

#: List of fields from `ALLOWED_SORTS` that can be sorted by simply using
#: `order_by(field)`
SIMPLY_SORTED = ['units']

#
# Store States
#

# Store just created, not parsed yet
NEW = 0
# Store just parsed, units added but no quality checks were run
PARSED = 1
# Quality checks run
CHECKED = 2

# Resolve conflict flags for Store.update
POOTLE_WINS = 1
SOURCE_WINS = 2

LANGUAGE_REGEX = r"[^/]{2,255}"
PROJECT_REGEX = r"[^/]{1,255}"

# Unit States
#: Unit is no longer part of the store
OBSOLETE = -100
#: Empty unit
UNTRANSLATED = 0
#: Marked as fuzzy, typically means translation needs more work
FUZZY = 50
#: Unit is fully translated
TRANSLATED = 200

# Map for retrieving natural names for unit states
STATES_MAP = {
    OBSOLETE: _("Obsolete"),
    UNTRANSLATED: _("Untranslated"),
    FUZZY: _("Needs work"),
    TRANSLATED: _("Translated"),
}

STATES_NAMES = {
    OBSOLETE: "obsolete",
    UNTRANSLATED: "untranslated",
    FUZZY: "fuzzy",
    TRANSLATED: "translated"}

# Default store priority - used by vfolders atm
#  - valid range = 0 < n <= 999.99
DEFAULT_PRIORITY = 1.0
