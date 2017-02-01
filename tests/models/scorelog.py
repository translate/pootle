# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pytest_pootle.factories import SubmissionFactory

from pootle_statistics.models import (
    ScoreLog, SubmissionTypes, SubmissionFields)


TEST_EDIT_TYPES = (SubmissionTypes.NORMAL, SubmissionTypes.SYSTEM,
                   SubmissionTypes.UPLOAD)


@pytest.mark.parametrize('submission_type', TEST_EDIT_TYPES)
@pytest.mark.django_db
def test_record_submission(member, submission_type, store0):
    store = store0
    unit = store.units.first()

    submission_params = {
        'store': store,
        'unit': unit,
        'field': SubmissionFields.TARGET,
        'type': submission_type,
        'old_value': unit.target,
        'new_value': 'New target',
        'submitter': member,
        'translation_project': store.translation_project,
    }

    sub = SubmissionFactory(**submission_params)
    assert ScoreLog.objects.filter(submission=sub).count() == 1
