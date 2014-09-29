#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2004-2012 Zuza Software Foundation
#
# This file is part of translate.
#
# translate is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# translate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with translate; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import os

from django.conf import settings
from django.utils.translation import ugettext_lazy as _


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
    if p.startswith(settings.PODIRECTORY):
        return p[len(add_trailing_slash(settings.PODIRECTORY)):]
    else:
        return p


def absolute_real_path(p):
    if not p.startswith(settings.PODIRECTORY):
        return os.path.join(settings.PODIRECTORY, p)
    else:
        return p


def suggestions_sum(queryset):
    total = 0
    for item in queryset:
        total += item.get_suggestion_count()

    return total


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


def get_sugg_list(unit):
    """Get suggested translations and rated scores for the given unit.

    :return: List of tuples containing the suggestion and the score for
             it in case it's a terminology project. Otherwise the score
             part is filled with False values.
    """
    sugg_list = []
    scores = {}
    suggestions = unit.get_suggestions()

    for sugg in suggestions:
        score = scores.get(sugg.id, False)
        sugg_list.append((sugg, score))

    return sugg_list
