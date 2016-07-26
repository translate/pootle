# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest


@pytest.fixture
def no_formats():
    from pootle.core.delegate import formats
    from pootle_format.models import Format

    Format.objects.all().delete()
    formats.get().clear()


@pytest.fixture
def format_registry():
    from pootle.core.delegate import formats

    format_registry = formats.get()
    format_registry.initialize()
    return format_registry
