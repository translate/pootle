# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle_store.models import QualityCheck


@pytest.mark.django_db
def test_qualitycheck(store0):
    unit = store0.units.first()
    qc = QualityCheck.objects.create(
        unit=unit,
        name="foo")
    assert qc.unit == unit
    assert qc.name == "foo"
    assert qc.false_positive is False
    assert str(qc) == "foo"
