# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.dispatch import receiver

from pootle.core.delegate import check_updater, crud, lifecycle
from pootle.core.signals import (
    create, delete, toggle, update_checks, update_data)
from pootle_store.models import QualityCheck, Store, Unit
from pootle_translationproject.models import TranslationProject


@receiver(delete, sender=QualityCheck)
def handle_qc_delete(**kwargs):
    crud.get(QualityCheck).delete(**kwargs)


@receiver(create, sender=QualityCheck)
def handle_qc_create(**kwargs):
    crud.get(QualityCheck).create(**kwargs)


@receiver(update_checks, sender=Unit)
def handle_unit_checks(**kwargs):
    unit = kwargs["instance"]
    keep_false_positives = kwargs.get("keep_false_positives", False)
    unit.update_qualitychecks(keep_false_positives=keep_false_positives)


@receiver(toggle, sender=QualityCheck)
def handle_toggle_quality_check(**kwargs):
    check = kwargs["instance"]
    false_positive = kwargs["false_positive"]
    unit = check.unit
    reviewer = unit.change.reviewed_by
    unit_lifecycle = lifecycle.get(Unit)(unit)
    subs = []
    check.false_positive = false_positive
    check.save()
    if check.false_positive:
        subs.append(
            unit_lifecycle.sub_mute_qc(quality_check=check,
                                       submitter=reviewer))
    else:
        subs.append(
            unit_lifecycle.sub_unmute_qc(quality_check=check,
                                         submitter=reviewer))
    unit_lifecycle.save_subs(subs=subs)
    store = unit.store
    update_data.send(store.__class__, instance=store)


@receiver(update_checks, sender=Store)
def store_checks_handler(**kwargs):
    store = kwargs["instance"]
    check_updater.get(Store)(
        store,
        units=kwargs.get("units"),
        check_names=kwargs.get("check_names")).update(
            clear_unknown=kwargs.get("clear_unknown", False),
            update_data_after=kwargs.get("update_data_after", False))


@receiver(update_checks, sender=TranslationProject)
def tp_checks_handler(**kwargs):
    tp = kwargs["instance"]
    check_updater.get(TranslationProject)(
        translation_project=tp,
        stores=kwargs.get("stores"),
        check_names=kwargs.get("check_names")).update(
            clear_unknown=kwargs.get("clear_unknown", False),
            update_data_after=kwargs.get("update_data_after", False))
