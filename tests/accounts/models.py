# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pytest_pootle.factories import UserFactory

from pootle.core.views.display import ActionDisplay
from pootle.i18n.dates import timesince
from pootle_statistics.models import Submission


@pytest.mark.django_db
def test_model_user_last_event(member):
    last_submission = Submission.objects.filter(submitter=member).last()
    last_event = member.last_event()
    assert isinstance(last_event, ActionDisplay)
    assert last_event.action == last_submission.get_submission_info()

    last_event = member.last_event(locale="zu")
    assert isinstance(last_event, ActionDisplay)
    assert last_event.action == last_submission.get_submission_info()
    assert last_event.since == timesince(last_event.action["mtime"], "zu")
    user = UserFactory()
    assert not user.last_event()
