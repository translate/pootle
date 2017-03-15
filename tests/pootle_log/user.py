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
def test_user_log(admin):
    user_log = log.get(admin.__class__)(admin)
    assert isinstance(user_log, UserLog)
    assert list(user_log.get_events())
    suggestions = admin.suggestions.all() | admin.reviews.all()
    assert (
        list(user_log.suggestion_qs.values_list("pk", flat=True))
        == list(suggestions.values_list("pk", flat=True)))
    assert (
        list(user_log.submission_qs.values_list("pk", flat=True))
        == list(admin.submission_set.values_list("pk", flat=True)))
