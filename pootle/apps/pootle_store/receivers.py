# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from hashlib import md5

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils.encoding import force_bytes

from pootle.core.delegate import lifecycle, uniqueid
from pootle.core.models import Revision
from pootle.core.signals import update_checks, update_data

from .constants import FUZZY, TRANSLATED, UNTRANSLATED
from .models import Suggestion, Unit, UnitChange, UnitSource


@receiver(post_save, sender=Suggestion)
def handle_suggestion_added(**kwargs):
    created = kwargs.get("created")
    if not created:
        return
    store = kwargs["instance"].unit.store
    update_data.send(store.__class__, instance=store)


@receiver(post_save, sender=Suggestion)
def handle_suggestion_accepted(**kwargs):
    created = kwargs.get("created")
    suggestion = kwargs["instance"]
    if created or not suggestion.is_accepted:
        return
    update_data.send(
        suggestion.unit.store.__class__,
        instance=suggestion.unit.store)


@receiver(pre_save, sender=UnitSource)
def handle_unit_source_pre_save(**kwargs):
    unit_source = kwargs["instance"]
    created = not unit_source.pk
    unit = unit_source.unit
    if created:
        unit_source.creation_revision = unit.revision
    if created or unit.source_updated:
        unit_source.source_hash = md5(force_bytes(unit.source_f)).hexdigest()
        unit_source.source_length = len(unit.source_f)
        unit_source.source_wordcount = (
            unit.counter.count_words(unit.source_f.strings)
            or 0)


@receiver(pre_save, sender=Unit)
def handle_unit_pre_save(**kwargs):
    unit = kwargs["instance"]
    auto_translated = False

    if unit.source_updated:
        # update source related fields
        wc = unit.counter.count_words(unit.source_f.strings)
        if not wc and not bool(filter(None, unit.target_f.strings)):
            # auto-translate untranslated strings
            unit.target = unit.source
            unit.state = FUZZY
            auto_translated = True
    if unit.target_updated:
        # update target related fields
        unit.target_wordcount = unit.counter.count_words(
            unit.target_f.strings)
        unit.target_length = len(unit.target_f)
        if filter(None, unit.target_f.strings):
            if unit.state == UNTRANSLATED:
                unit.state = TRANSLATED
        else:
            # if it was TRANSLATED then set to UNTRANSLATED
            if unit.state > FUZZY:
                unit.state = UNTRANSLATED

    # Updating unit from the .po file set its revision property to
    # a new value (the same for all units during its store updated)
    # since that change doesn't require further sync but note that
    # auto_translated units require further sync
    update_revision = (
        unit.revision is None
        or (not unit.revision_updated
            and (unit.updated and not auto_translated)))
    if update_revision:
        unit.revision = Revision.incr()

    if unit.index is None:
        unit.index = unit.store.max_index() + 1
    unitid = uniqueid.get(unit.__class__)(unit)
    if unitid.changed:
        unit.setid(unitid.getid())


@receiver(post_save, sender=UnitChange)
def handle_unit_change(**kwargs):
    unit_change = kwargs["instance"]
    unit = unit_change.unit
    created = not unit._frozen.pk

    if not created:
        lifecycle.get(Unit)(unit).change()
    if not unit.source_updated and not unit.target_updated:
        return
    new_untranslated = (created and unit.state == UNTRANSLATED)
    if not new_untranslated:
        update_checks.send(unit.__class__, instance=unit)
    if unit.istranslated():
        unit.update_tmserver()
