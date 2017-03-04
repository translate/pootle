# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle_statistics.models import ScoreLog, SubmissionTypes


TEST_EDIT_TYPES = (SubmissionTypes.WEB, SubmissionTypes.SYSTEM,
                   SubmissionTypes.UPLOAD)


@pytest.mark.parametrize('submission_type', TEST_EDIT_TYPES)
@pytest.mark.django_db
def test_record_submission(member, submission_type, store0):
    store = store0
    unit = store.units.first()
    assert ScoreLog.objects.filter(
        submission=unit.submission_set.first()).count() == 1
