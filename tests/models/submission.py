#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.utils import timezone

from pytest_pootle.factories import SubmissionFactory

from pootle_statistics.models import (Submission, SubmissionFields,
                                      SubmissionTypes)
from pootle_store.util import TRANSLATED, UNTRANSLATED


def _create_comment_submission(unit, user, creation_time, comment):
    sub = Submission(
        creation_time=creation_time,
        translation_project=unit.store.translation_project,
        submitter=user,
        unit=unit,
        store=unit.store,
        field=SubmissionFields.COMMENT,
        type=SubmissionTypes.NORMAL,
        new_value=comment,
    )
    sub.save()
    return sub


@pytest.mark.django_db
def test_submission_ordering(en_tutorial_po, member, no_submissions):
    """Submissions with same creation_time should order by pk
    """

    at_time = timezone.now()
    unit = en_tutorial_po.units[0]
    _create_comment_submission(unit, member, at_time, "Comment 3")
    _create_comment_submission(unit, member, at_time, "Comment 2")
    _create_comment_submission(unit, member, at_time, "Comment 1")
    unit = en_tutorial_po.units[0]

    # Object manager test
    assert Submission.objects.count() == 3
    assert (Submission.objects.first().creation_time
            == Submission.objects.last().creation_time)
    assert (Submission.objects.latest().pk
            > Submission.objects.earliest().pk)

    # Related manager test
    assert (unit.submission_set.latest().pk
            > unit.submission_set.earliest().pk)

    # Passing field_name test
    assert (unit.submission_set.earliest("new_value").new_value
            == "Comment 1")
    assert (unit.submission_set.latest("new_value").new_value
            == "Comment 3")
    assert (unit.submission_set.earliest("pk").new_value
            == "Comment 3")
    assert (unit.submission_set.latest("pk").new_value
            == "Comment 1")


def test_max_similarity():
    """Tests that the maximum similarity is properly returned."""
    submission = SubmissionFactory.build(
        similarity=0,
        mt_similarity=0,
    )
    assert submission.max_similarity == 0

    submission = SubmissionFactory.build(
        similarity=0.5,
        mt_similarity=0.6,
    )
    assert submission.max_similarity == 0.6

    submission = SubmissionFactory.build(
        similarity=0.5,
        mt_similarity=None,
    )
    assert submission.max_similarity == 0.5

    submission = SubmissionFactory.build(
        similarity=None,
        mt_similarity=None,
    )
    assert submission.max_similarity == 0


def test_needs_scorelog():
    """Tests if the submission needs to be logged or not."""
    # Changing the STATE from UNTRANSLATED won't record any logs
    submission = SubmissionFactory.build(
        field=SubmissionFields.STATE,
        type=SubmissionTypes.NORMAL,
        old_value=UNTRANSLATED,
        new_value=TRANSLATED,
    )
    assert not submission.needs_scorelog()

    # Changing other fields (or even STATE, in a different direction) should
    # need to record a score log
    submission = SubmissionFactory.build(
        field=SubmissionFields.STATE,
        type=SubmissionTypes.NORMAL,
        old_value=TRANSLATED,
        new_value=UNTRANSLATED,
    )
    assert submission.needs_scorelog()

    submission = SubmissionFactory.build(
        field=SubmissionFields.TARGET,
        type=SubmissionTypes.SUGG_ADD,
        old_value=u'',
        new_value=u'',
    )
    assert submission.needs_scorelog()
