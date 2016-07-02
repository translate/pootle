# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest


@pytest.fixture
def anon_submission_unit():
    from django.contrib.auth import get_user_model
    from django.utils import timezone
    from pootle_statistics.models import SubmissionTypes
    from pootle_store.models import Store

    User = get_user_model()
    anon = User.objects.get(username="nobody")
    unit = Store.objects.live().first().units.first()
    old_target = unit.target
    old_state = unit.state
    unit.target_f = "Updated %s" % old_target
    unit._target_updated = True
    unit.store.record_submissions(
        unit, old_target, old_state,
        timezone.now(), anon,
        SubmissionTypes.NORMAL)
    unit.save()
