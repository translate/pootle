# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle.core.delegate import check_updater
from pootle_checks.utils import TPQCUpdater, StoreQCUpdater
from pootle_store.constants import OBSOLETE
from pootle_store.models import QualityCheck


@pytest.mark.django_db
def test_tp_qualitycheck_updater(tp0):
    qc_updater = check_updater.get(tp0.__class__)
    assert qc_updater is TPQCUpdater
    updater = qc_updater(translation_project=tp0)
    updater.update()
    checks = QualityCheck.objects.filter(unit__store__translation_project=tp0)
    original_checks = checks.delete()[0]
    assert original_checks
    updater.update()
    assert checks.count() == original_checks
    # make unit obsolete
    original_revision = tp0.directory.revisions.filter(
        key="stats").values_list("value", flat=True).first()
    check = checks[0]
    unit = check.unit
    unit.__class__.objects.filter(pk=unit.pk).update(state=OBSOLETE)
    updater.update(update_data_after=True)
    assert check.__class__.objects.filter(pk=check.pk).count() == 0
    new_revision = tp0.directory.revisions.filter(
        key="stats").values_list("value", flat=True).first()
    assert original_revision != new_revision
    # set to unknown check
    check = checks[0]
    check.name = "DOES_NOT_EXIST"
    check.save()
    updater.update()
    assert check.__class__.objects.filter(pk=check.pk).count() == 0
    # fix a check
    check = checks.filter(name="printf")[0]
    unit = check.unit
    unit.__class__.objects.filter(pk=unit.pk).update(target_f=unit.source_f)
    updater.update()
    assert check.__class__.objects.filter(pk=check.pk).count() == 0

    # obsolete units in 2 stores - but only update checks for one store
    store_ids = checks.filter(name="printf").values_list(
        "unit__store", flat=True).distinct()[:2]
    check1 = checks.filter(name="printf").filter(
        unit__store_id=store_ids[0]).first()
    check2 = checks.filter(name="printf").filter(
        unit__store_id=store_ids[1]).first()
    unit1 = check1.unit
    store1 = unit1.store
    unit2 = check2.unit
    store2 = unit2.store
    store1.units.filter(id=unit1.id).update(state=OBSOLETE)
    store2.units.filter(id=unit2.id).update(state=OBSOLETE)
    qc_updater(
        translation_project=tp0,
        stores=[store1.id]).update()
    assert check.__class__.objects.filter(pk=check1.pk).count() == 0
    assert check.__class__.objects.filter(pk=check2.pk).count() == 1


@pytest.mark.django_db
def test_store_qualitycheck_updater(tp0, store0):
    qc_updater = check_updater.get(store0.__class__)
    assert qc_updater is StoreQCUpdater
    QualityCheck.objects.filter(unit__store__translation_project=tp0).delete()
    updater = qc_updater(store=store0)
    updater.update()
    checks = QualityCheck.objects.filter(unit__store=store0)
    original_checks = checks.delete()[0]
    assert original_checks
    updater.update()
    assert checks.count() == original_checks
    # make unit obsolete
    original_revision = store0.parent.revisions.filter(
        key="stats").values_list("value", flat=True).first()
    check = checks[0]
    unit = check.unit
    unit.__class__.objects.filter(pk=unit.pk).update(state=OBSOLETE)
    updater.update(update_data_after=True)
    assert check.__class__.objects.filter(pk=check.pk).count() == 0
    new_revision = tp0.directory.revisions.filter(
        key="stats").values_list("value", flat=True).first()
    assert original_revision != new_revision
    updater.update(update_data_after=True)
    newest_revision = tp0.directory.revisions.filter(
        key="stats").values_list("value", flat=True).first()
    assert newest_revision == new_revision
