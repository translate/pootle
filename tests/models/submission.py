#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle_statistics.models import SubmissionTypes, SubmissionFields
from pootle_store.util import TRANSLATED, UNTRANSLATED

from ..factories import SubmissionFactory


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

    # Changing other fields (or even STATE, in a different direction)
    # should need to record a score log
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
