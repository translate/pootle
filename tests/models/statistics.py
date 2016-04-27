# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle_statistics.models import Submission


@pytest.mark.django_db
def test_submission_repr():
    submission = Submission.objects.first()
    assert (
        "<Submission: %s (%s)>"
        % (submission.creation_time.strftime("%Y-%m-%d %H:%M"),
           unicode(submission.submitter))
        == repr(submission))
