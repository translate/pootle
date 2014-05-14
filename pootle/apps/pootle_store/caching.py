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

from .util import (FUZZY, OBSOLETE, TRANSLATED, TRANSLATION_ADDED,
                   TRANSLATION_DELETED, TRANSLATION_EDITED, UNTRANSLATED)


def count_words(strings):
    return sum(wordcount(string) for string in strings)


def unit_delete_cache(unit):
    """
    Triggered on unit.delete()
    Decrement the cache columns by the appropriate amount
    """

    wordcount = count_words(unit.source_f.strings)

    unit.store.total_wordcount -= wordcount

    if unit.state == FUZZY:
        unit.store.fuzzy_wordcount -= wordcount
    elif unit.state == TRANSLATED:
        unit.store.translated_wordcount -= wordcount


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

    if not orig:
        # New instance. Calculate everything.
        unit.store.total_wordcount += source_wordcount
        if unit.state == TRANSLATED:
            unit.store.translated_wordcount += source_wordcount
        elif unit.state == FUZZY:
            unit.store.fuzzy_wordcount += source_wordcount

    if unit._source_updated:
        # update source related fields
        unit.source_hash = md5(unit.source_f.encode("utf-8")).hexdigest()
        unit.store.total_wordcount += difference
        unit.source_wordcount = source_wordcount
        unit.source_length = len(unit.source_f)
        if not orig:
            unit.store.total_wordcount += difference

    if orig:
        # Case 1: Unit was not translated before
        if orig.state == UNTRANSLATED:
            if unit.state == UNTRANSLATED:
                pass
            elif unit.state == FUZZY:
                unit.store.fuzzy_wordcount += source_wordcount
            elif unit.state == TRANSLATED:
                unit.store.translated_wordcount += source_wordcount

        # Case 2: Unit was fuzzy before
        elif orig.state == FUZZY:
            if unit.state == UNTRANSLATED:
                unit.store.fuzzy_wordcount -= source_wordcount
            elif unit.state == FUZZY:
                unit.store.fuzzy_wordcount += difference
            elif unit.state == TRANSLATED:
                unit.store.fuzzy_wordcount -= source_wordcount
                unit.store.translated_wordcount += source_wordcount

        # Case 3: Unit was translated before
        elif orig.state == TRANSLATED:
            if unit.state == UNTRANSLATED:
                unit.store.translated_wordcount -= source_wordcount
            elif unit.state == FUZZY:
                unit.store.translated_wordcount -= source_wordcount
                unit.store.fuzzy_wordcount += source_wordcount
            elif unit.state == TRANSLATED:
                unit.store.translated_wordcount += difference

        unit.store.save()

    # Update the unit state
    if unit._target_updated:
        unit.target_length = len(unit.target_f)
        # Triggered when suggestions are accepted...
        # what exactly is happening here?
        if filter(None, unit.target_f.strings):
            if unit.state == UNTRANSLATED:
                unit.state = TRANSLATED
                # TODO do this in the previous block. Properly.
                unit.store.translated_wordcount += source_wordcount
                unit.store.save()
                unit.store.translation_project.translated_wordcount += source_wordcount
                unit.store.translation_project.save()
                if not hasattr(unit, '_save_action'):
                    unit._save_action = TRANSLATION_ADDED
            else:
                if not hasattr(unit, '_save_action'):
                    unit._save_action = TRANSLATION_EDITED
        else:
            unit._save_action = TRANSLATION_DELETED
            # if it was TRANSLATED then set to UNTRANSLATED
            if unit.state > FUZZY:
                unit.state = UNTRANSLATED
