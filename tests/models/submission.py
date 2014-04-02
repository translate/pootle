#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2014 Evernote Corporation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

import pytest

from pootle_statistics.models import SubmissionTypes, SubmissionFields
from pootle_store.util import TRANSLATED, UNTRANSLATED

from ..factories import SubmissionFactory


@pytest.mark.django_db
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

@pytest.mark.django_db
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
