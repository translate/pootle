# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle_store.constants import UNTRANSLATED


@pytest.mark.django_db
def test_store_update_new_unit_revision(store0):
    new_store = store0.deserialize(store0.serialize())
    new_unit = new_store.units[1].copy()
    new_unit.source = "INSERTED UNIT"
    new_store.units = new_store.units + [new_unit]
    store0.update(
        new_store,
        store_revision=store0.data.max_unit_revision + 1)
    new_unit = store0.units.get(source_f="INSERTED UNIT")
    creation_revision = new_unit.unit_source.creation_revision
    assert creation_revision
    assert creation_revision == store0.data.max_unit_revision
    new_unit.source_f = "NEW SOURCE"
    new_unit.save()
    unit_source = new_unit.unit_source.__class__.objects.get(
        pk=new_unit.unit_source.pk)
    assert new_unit.revision > unit_source.creation_revision
    assert unit_source.creation_revision == creation_revision


@pytest.mark.django_db
def test_store_update_source_change_subs(store0, member, system):
    unit = store0.units.filter(state=UNTRANSLATED).first()
    unit.source = "NEW SOURCE"
    unit.save()
    created_sub = unit.submission_set.latest()
    assert created_sub.submitter == system
    unit.source = "SOURCE CHANGED BY USER"
    unit.save(user=member)
    created_sub = unit.submission_set.latest()
    assert created_sub.submitter == member
