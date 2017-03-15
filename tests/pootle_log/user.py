# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle.core.delegate import log

from pootle_log.utils import UserLog


@pytest.mark.django_db
def test_user_log(member2):
    user_log = log.get(member2.__class__)(member2)
    assert isinstance(user_log, UserLog)
    assert list(user_log.get_events())
