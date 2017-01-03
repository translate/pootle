# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.urls import reverse

from pootle.core.delegate import scores
from pootle_profile.views import UserDetailView


@pytest.mark.django_db
def test_view_user_detail(client, member, system):
    response = client.get(
        reverse(
            'pootle-user-profile',
            kwargs=dict(username=member.username)))
    assert isinstance(response.context["view"], UserDetailView)
    user_scores = scores.get(member.__class__)(member)
    assert response.context["user_score"] == user_scores.public_score
    assert response.context["user_top_language"] == user_scores.top_language
