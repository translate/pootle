# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pytest_pootle.factories import ScoreLogFactory, SubmissionFactory

from pootle_statistics.models import (ScoreLog, SubmissionTypes, SubmissionFields,
                                      SIMILARITY_THRESHOLD)


TEST_EDIT_TYPES = (SubmissionTypes.NORMAL, SubmissionTypes.SYSTEM,
                   SubmissionTypes.UPLOAD)


@pytest.mark.parametrize('submission_type', TEST_EDIT_TYPES)
@pytest.mark.django_db
def test_record_submission(member, submission_type):
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
    }

    sub = SubmissionFactory(**submission_params)
    assert ScoreLog.objects.filter(submission=sub).count() == 1


@pytest.mark.parametrize('similarity', (0, 0.1, 0.49, 0.5, 0.51, 0.6, 1))
def test_get_similarity(similarity):
    score_log = ScoreLogFactory.build(similarity=similarity)
    if similarity >= SIMILARITY_THRESHOLD:
        assert score_log.get_similarity() == similarity
    else:
        assert score_log.get_similarity() == 0


@pytest.mark.parametrize('similarity, mt_similarity', [(0, 1), (0.5, 0.5), (1, 0)])
def test_is_similarity_taken_from_mt(similarity, mt_similarity):
    submission = SubmissionFactory.build(similarity=similarity,
                                         mt_similarity=mt_similarity)
    score_log = ScoreLogFactory.build(submission=submission)
    if submission.similarity < submission.mt_similarity:
        assert score_log.is_similarity_taken_from_mt()
    else:
        assert not score_log.is_similarity_taken_from_mt()
