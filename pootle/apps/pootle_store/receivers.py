# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from pootle.core.delegate import uniqueid
from pootle.core.log import UNIT_ADDED, action_log
from pootle.core.signals import update_data

from .constants import UNTRANSLATED
from .models import Suggestion, Unit, UnitChange, UnitSource


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
    if unit.index is None:
        unit.index = unit.store.max_index() + 1
    unitid = uniqueid.get(unit.__class__)(unit)
    if unitid.changed:
        unit.setid(unitid.getid())


@receiver(post_save, sender=UnitSource)
def handle_unit_create(**kwargs):
    if not kwargs["created"]:
        return
    unit_source = kwargs["instance"]
    unit = unit_source.unit
    action_log(
        user=unit_source.created_by,
        action=UNIT_ADDED,
        lang=unit.store.translation_project.language.code,
        unit=unit.id,
        translation=unit.target_f,
        path=unit.store.pootle_path)


@receiver(post_save, sender=UnitChange)
def handle_unit_change(**kwargs):
    unit_change = kwargs["instance"]
    unit = unit_change.unit
    if not unit.source_updated and not unit.target_updated:
        return
    created = not unit._frozen.pk
    new_untranslated = (created and unit.state == UNTRANSLATED)
    if not new_untranslated:
        unit.update_qualitychecks()
    if unit.istranslated():
        unit.update_tmserver()
