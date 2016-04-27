# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest


@pytest.fixture(scope='session', autouse=True)
def delete_pattern():
    """Adds the no-op `delete_pattern()` method to `LocMemCache`."""
    from django.core.cache.backends.locmem import LocMemCache
    LocMemCache.delete_pattern = lambda x, y: 0
