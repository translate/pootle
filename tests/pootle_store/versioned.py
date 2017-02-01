# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle.core.delegate import versioned
from pootle_store.models import Store


@pytest.mark.django_db
def test_versioned_store(store0):
    versions = versioned.get(Store)(store0)
    unit = store0.units[0]
    rev0 = dict(
        revision=store0.data.max_unit_revision,
        translated=unit.istranslated(),
        target=unit.target,
        fuzzy=unit.isfuzzy(),
        obsolete=unit.isobsolete())
    unit.target = "changed target"
    unit.save()
    old_store = versions.at_revision(rev0["revision"])
    old_unit = old_store.findid(unit.getid())
    assert old_unit.target == rev0["target"]
    assert old_unit.isfuzzy() == rev0["fuzzy"]
    assert old_unit.istranslated() == rev0["translated"]
    assert old_unit.isobsolete() == rev0["obsolete"]

    unit = store0.units[0]
    rev1 = dict(
        revision=store0.data.max_unit_revision,
        translated=unit.istranslated(),
        target=unit.target,
        fuzzy=unit.isfuzzy(),
        obsolete=unit.isobsolete())
    unit.target = "changed target again"
    unit.save()
    old_store = versions.at_revision(rev1["revision"])
    old_unit = old_store.findid(unit.getid())
    assert old_unit.target == rev1["target"]
    assert old_unit.isfuzzy() == rev1["fuzzy"]
    assert old_unit.istranslated() == rev1["translated"]
    assert old_unit.isobsolete() == rev1["obsolete"]

    unit = store0.units[0]
    rev2 = dict(
        revision=store0.data.max_unit_revision,
        translated=unit.istranslated(),
        target=unit.target,
        fuzzy=unit.isfuzzy(),
        obsolete=unit.isobsolete())
    unit.markfuzzy()
    unit.save()
    old_store = versions.at_revision(rev2["revision"])
    old_unit = old_store.findid(unit.getid())
    assert old_unit.target == rev2["target"]
    assert old_unit.isfuzzy() == rev2["fuzzy"]
    assert old_unit.istranslated() == rev2["translated"]
    assert old_unit.isobsolete() == rev2["obsolete"]

    unit = store0.units[0]
    rev3 = dict(
        revision=store0.data.max_unit_revision,
        translated=unit.istranslated(),
        target=unit.target,
        fuzzy=unit.isfuzzy(),
        obsolete=unit.isobsolete())
    unit.markfuzzy(False)
    unit.save()
    old_store = versions.at_revision(rev3["revision"])
    old_unit = old_store.findid(unit.getid())
    assert old_unit.target == rev3["target"]
    assert old_unit.isfuzzy() == rev3["fuzzy"]
    assert old_unit.istranslated() == rev3["translated"]
    assert old_unit.isobsolete() == rev3["obsolete"]
    old_store = versions.at_revision(rev2["revision"])
    old_unit = old_store.findid(unit.getid())
    assert old_unit.target == rev2["target"]
    assert old_unit.isfuzzy() == rev2["fuzzy"]
    assert old_unit.istranslated() == rev2["translated"]
    assert old_unit.isobsolete() == rev2["obsolete"]
    old_store = versions.at_revision(rev1["revision"])
    old_unit = old_store.findid(unit.getid())
    assert old_unit.target == rev1["target"]
    assert old_unit.isfuzzy() == rev1["fuzzy"]
    assert old_unit.istranslated() == rev1["translated"]
    assert old_unit.isobsolete() == rev1["obsolete"]
    old_store = versions.at_revision(rev0["revision"])
    old_unit = old_store.findid(unit.getid())
    assert old_unit.target == rev0["target"]
    assert old_unit.isfuzzy() == rev0["fuzzy"]
    assert old_unit.istranslated() == rev0["translated"]
    assert old_unit.isobsolete() == rev0["obsolete"]
