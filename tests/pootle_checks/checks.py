# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle_checks.utils import QualityCheckUpdater
from pootle_store.constants import OBSOLETE
from pootle_store.models import QualityCheck


@pytest.mark.django_db
def test_tp_qualitycheck_updater(tp0):
    updater = QualityCheckUpdater(translation_project=tp0)
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
    updater.update()
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


@pytest.mark.django_db
def test_store_qualitycheck_updater(tp0, store0):
    QualityCheck.objects.filter(unit__store__translation_project=tp0).delete()
    updater = QualityCheckUpdater(units=store0.unit_set.all())
    updater.update()
    checks = QualityCheck.objects.filter(unit__store=store0)
    original_checks = checks.delete()[0]
    assert original_checks
    updater.update()
    assert checks.count() == original_checks
    assert (
        QualityCheck.objects.filter(unit__store__translation_project=tp0).count()
        == original_checks)
