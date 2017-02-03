# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle.core.user import get_system_user, get_system_user_id


@pytest.mark.django_db
def test_user_get_system_user(system):
    assert get_system_user() == system
    assert get_system_user_id() == system.id
