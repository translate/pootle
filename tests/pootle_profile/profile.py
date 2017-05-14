# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle.core.delegate import profile
from pootle_profile.utils import UserMembership, UserProfile
from pootle_score.utils import UserScores


@pytest.mark.django_db
def test_profile_user(member):
    user_profile = profile.get(member.__class__)(member)
    assert isinstance(user_profile, UserProfile)
    assert user_profile.user == member
    user_membership = user_profile.membership
    assert isinstance(user_membership, UserMembership)
    assert user_membership.user == member
    user_scores = user_profile.scores
    assert isinstance(user_scores, UserScores)
    assert user_scores.context == member
    assert user_profile.display_name == member.display_name
