#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2013 Zuza Software Foundation
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

"""
Caching functionality for Unit model
"""

from hashlib import md5

from translate.storage.statsdb import wordcount

from pootle.core import log
from .util import FUZZY, OBSOLETE, TRANSLATED, UNTRANSLATED


def count_words(strings):
    return sum(wordcount(string) for string in strings)


def unit_delete_cache(unit):
    """
    Triggered on unit.delete()
    Decrement the cache columns by the appropriate amount
    """
    if unit.state == OBSOLETE or unit.id is None:
        # Do nothing.
        return

    wordcount = count_words(unit.source_f.strings)

    unit.store.total_wordcount -= wordcount
    unit.store.translation_project.total_wordcount -= wordcount

    if unit.state == FUZZY:
        unit.store.fuzzy_wordcount -= wordcount
        unit.store.translation_project.fuzzy_wordcount -= wordcount
    elif unit.state == TRANSLATED:
        unit.store.translated_wordcount -= wordcount
        unit.store.translation_project.translated_wordcount -= wordcount

    if unit.has_critical_failures:
        unit.store.failing_critical_count -= 1
        unit.store.translation_project.failing_critical_count -= 1

    unit.store.save()
    unit.store.translation_project.save()


def unit_update_cache(unit):
    """
    Update the Store (and related) cache columns when a Unit is modified
    Triggered on unit.save() before anything is saved
    """
    if unit.id:
        orig = unit.__class__.objects.get(id=unit.id)
    else:
        orig = None

    source_wordcount = count_words(unit.source_f.strings)
    difference = source_wordcount - unit.source_wordcount

    if not orig and unit.state != OBSOLETE:
        # New instance. Calculate everything.
        unit.store.total_wordcount += source_wordcount
        unit.store.translation_project.total_wordcount += source_wordcount
        if unit.state == TRANSLATED:
            unit.store.translated_wordcount += source_wordcount
            unit.store.translation_project.translated_wordcount += source_wordcount
        elif unit.state == FUZZY:
            unit.store.fuzzy_wordcount += source_wordcount
            unit.store.translation_project.fuzzy_wordcount += source_wordcount

    if unit._source_updated and unit.state != OBSOLETE:
        # update source related fields
        unit.source_hash = md5(unit.source_f.encode("utf-8")).hexdigest()
        unit.store.total_wordcount += difference
        unit.store.translation_project.total_wordcount += difference
        unit.source_wordcount = source_wordcount
        unit.source_length = len(unit.source_f)
        if not orig:
            unit.store.total_wordcount += difference
            unit.store.translation_project.total_wordcount += difference

    if orig:
        # Case 1: Unit was not translated or was obsolete before
        if orig.state in (UNTRANSLATED, OBSOLETE):
            if unit.state in (UNTRANSLATED, OBSOLETE):
                pass
            elif unit.state == FUZZY:
                unit.store.fuzzy_wordcount += source_wordcount
                unit.store.translation_project.fuzzy_wordcount += source_wordcount
            elif unit.state == TRANSLATED:
                unit.store.translated_wordcount += source_wordcount
                unit.store.translation_project.translated_wordcount += source_wordcount

        # Case 2: Unit was fuzzy before
        elif orig.state == FUZZY:
            if unit.state in (UNTRANSLATED, OBSOLETE):
                unit.store.fuzzy_wordcount -= source_wordcount
                unit.store.translation_project.fuzzy_wordcount -= source_wordcount
            elif unit.state == FUZZY:
                unit.store.fuzzy_wordcount += difference
                unit.store.translation_project.fuzzy_wordcount += difference
            elif unit.state == TRANSLATED:
                unit.store.fuzzy_wordcount -= source_wordcount
                unit.store.translation_project.fuzzy_wordcount -= source_wordcount
                unit.store.translated_wordcount += source_wordcount
                unit.store.translation_project.translated_wordcount += source_wordcount

        # Case 3: Unit was translated before
        elif orig.state == TRANSLATED:
            if unit.state in (UNTRANSLATED, OBSOLETE):
                unit.store.translated_wordcount -= source_wordcount
                unit.store.translation_project.translated_wordcount -= source_wordcount
            elif unit.state == FUZZY:
                unit.store.translated_wordcount -= source_wordcount
                unit.store.translation_project.translated_wordcount -= source_wordcount
                unit.store.fuzzy_wordcount += source_wordcount
                unit.store.translation_project.fuzzy_wordcount += source_wordcount
            elif unit.state == TRANSLATED:
                unit.store.translated_wordcount += difference
                unit.store.translation_project.translated_wordcount += difference

    # Update the unit state
    if unit._target_updated and unit.state != OBSOLETE:
        unit.target_length = len(unit.target_f)
        # Triggered when suggestions are accepted...
        # what exactly is happening here?
        if filter(None, unit.target_f.strings):
            if unit.state == UNTRANSLATED:
                unit.state = TRANSLATED
                # TODO do this in the previous block. Properly.
                unit.store.translated_wordcount += source_wordcount
                unit.store.translation_project.translated_wordcount += source_wordcount
                if not hasattr(unit, '_save_action'):
                    unit._save_action = log.TRANSLATION_ADDED
            else:
                if not hasattr(unit, '_save_action'):
                    unit._save_action = log.TRANSLATION_CHANGED
        else:
            unit._save_action = log.TRANSLATION_DELETED
            # if it was TRANSLATED then set to UNTRANSLATED
            if unit.state > FUZZY:
                unit.state = UNTRANSLATED

    unit.store.save()
    unit.store.translation_project.save()
