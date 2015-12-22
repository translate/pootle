#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from datetime import datetime

from pootle_statistics.models import ScoreLog, SubmissionTypes, SubmissionFields

from pootle_pytest.factories import SubmissionFactory


TEST_EDIT_TYPES = (SubmissionTypes.NORMAL, SubmissionTypes.SYSTEM,
                   SubmissionTypes.UPLOAD)


@pytest.mark.parametrize('submission_type', TEST_EDIT_TYPES)
@pytest.mark.django_db
def test_record_submission(site_matrix, member, submission_type):
    from pootle_store.models import Store
    store = Store.objects.first()
    unit = store.units.first()

    submission_params = {
        'store': store,
        'unit': unit,
        'field': SubmissionFields.TARGET,
        'type': submission_type,
        'old_value': unit.target,
        'new_value': 'New target',
        'similarity': 0,
        'mt_similarity': 0,
        'submitter': member,
        'translation_project': store.translation_project,
        'creation_time': datetime.now(),
    }

    sub = SubmissionFactory(**submission_params)
    assert ScoreLog.objects.filter(submission=sub).count() == 1
