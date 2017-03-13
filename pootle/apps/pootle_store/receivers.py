# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from hashlib import md5

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from pootle.core.delegate import lifecycle, uniqueid
from pootle.core.models import Revision
from pootle.core.signals import update_data
from pootle.core.utils.timezone import make_aware

from .constants import FUZZY, TRANSLATED, UNTRANSLATED
from .models import Suggestion, Unit, UnitChange


@receiver(post_save, sender=Suggestion)
def handle_suggestion_added(**kwargs):
    created = kwargs.get("created")
    if not created:
        return
    store = kwargs["instance"].unit.store
    update_data.send(store.__class__, instance=store)


@receiver(pre_save, sender=Unit)
def handle_unit_pre_save(**kwargs):
    unit = kwargs["instance"]
    auto_translated = False
    was_fuzzy = unit._frozen.state == FUZZY
    sysuser = get_user_model().objects.get_system_user()

    if unit.source_updated:
        # update source related fields
        unit.source_hash = md5(unit.source_f.encode("utf-8")).hexdigest()
        unit.source_length = len(unit.source_f)
        wc = unit.update_wordcount()
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
    if was_fuzzy:
        # set reviewer data if FUZZY has been removed only and
        # translation hasn't been updated
        unit.reviewed_on = make_aware(timezone.now())
        unit.reviewed_by = unit.reviewed_by or sysuser
    elif unit.state == FUZZY:
        # clear reviewer data if unit has been marked as FUZZY
        unit.reviewed_on = None
        unit.reviewed_by = None
    elif unit.state == UNTRANSLATED:
        # clear reviewer and translator data if translation
        # has been deleted
        unit.reviewed_on = None
        unit.reviewed_by = None
        unit.submitted_by = None
        unit.submitted_on = None

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
        unit.update_qualitychecks()
    if unit.istranslated():
        unit.update_tmserver()


@receiver(post_save, sender=Suggestion)
def handle_suggestion_accepted(**kwargs):
    suggestion = kwargs["instance"]
    if suggestion.state.name != "accepted":
        return
    suggestion.unit.submission_set.filter(
        revision=suggestion.unit.revision,
        submitter=suggestion.user).update(suggestion_id=suggestion.id)
