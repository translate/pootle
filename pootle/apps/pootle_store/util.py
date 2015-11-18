#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from pootle_misc.aggregate import sum_column

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


def add_trailing_slash(path):
    """If path does not end with /, add it and return."""

    if len(path) > 0 and path[-1] == os.sep:
        return path
    else:
        return path + os.sep


def relative_real_path(p):
    if p.startswith(settings.POOTLE_TRANSLATION_DIRECTORY):
        return p[len(add_trailing_slash(settings.POOTLE_TRANSLATION_DIRECTORY)):]
    else:
        return p


def absolute_real_path(p):
    if not p.startswith(settings.POOTLE_TRANSLATION_DIRECTORY):
        return os.path.join(settings.POOTLE_TRANSLATION_DIRECTORY, p)
    else:
        return p


def calc_total_wordcount(units):
    total = sum_column(units,
                       ['source_wordcount'], count=False)

    return total['source_wordcount'] or 0


def calc_untranslated_wordcount(units):
    untranslated = sum_column(units.filter(state=UNTRANSLATED),
                              ['source_wordcount'], count=False)

    return untranslated['source_wordcount'] or 0


def calc_fuzzy_wordcount(units):
    fuzzy = sum_column(units.filter(state=FUZZY),
                       ['source_wordcount'], count=False)

    return fuzzy['source_wordcount'] or 0


def calc_translated_wordcount(units):
    translated = sum_column(units.filter(state=TRANSLATED),
                            ['source_wordcount'],
                            count=False)

    return translated['source_wordcount'] or 0


def find_altsrcs(unit, alt_src_langs, store=None, project=None):
    from pootle_store.models import Unit

    store = store or unit.store
    project = project or store.translation_project.project

    altsrcs = Unit.objects.filter(
                    unitid_hash=unit.unitid_hash,
                    store__translation_project__project=project,
                    store__translation_project__language__in=alt_src_langs,
                    state=TRANSLATED) \
                          .select_related(
                                'store', 'store__translation_project',
                                'store__translation_project__language')

    if project.get_treestyle() == 'nongnu':
        altsrcs = filter(lambda x: x.store.path == store.path, altsrcs)

    return altsrcs


def get_change_str(changes):
    """Returns a formatted string for the non-zero items of a `changes`
    dictionary.

    If all elements are zero, `nothing changed` is returned.
    """
    res = [u'%s %d' % (key, changes[key])
           for key in changes if changes[key] > 0]

    if res:
        return ", ".join(res)

    return "no changed"


def parse_pootle_revision(store):
    if hasattr(store, "parseheader"):
        pootle_revision = store.parseheader().get("X-Pootle-Revision",
                                                  None)
        if pootle_revision is not None:
            return int(pootle_revision)
    return None
