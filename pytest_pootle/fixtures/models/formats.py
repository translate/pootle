# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest


@pytest.fixture
def po():
    from pootle_format.models import Format

    return Format.objects.get(name="po")


@pytest.fixture
def ts():
    from pootle_format.models import Format

    return Format.objects.get(name="ts")


@pytest.fixture
def po2():
    from pootle.core.delegate import formats

    registry = formats.get()

    # register po2
    return registry.register(
        "special_po_2", "po2", template_extension="pot2")


@pytest.fixture
def xliff():
    from pootle_format.models import Format

    return Format.objects.get(name="xliff")
