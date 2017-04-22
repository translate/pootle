# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.dispatch import receiver

from pootle.core.signals import toggle, update_checks, update_data
from pootle.core.delegate import check_updater, lifecycle
from pootle_store.models import QualityCheck, Unit
from pootle_translationproject.models import TranslationProject


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


@receiver(update_checks, sender=TranslationProject)
def tp_checks_handler(**kwargs):
    tp = kwargs["instance"]
    check_updater.get(TranslationProject)(
        translation_project=tp,
        check_names=kwargs.get("check_names")).update()
