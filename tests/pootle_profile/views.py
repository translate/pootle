# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.urls import reverse

from pootle_profile.utils import UserProfile
from pootle_profile.views import UserDetailView


@pytest.mark.django_db
def test_view_user_detail(client, member, system):
    response = client.get(
        reverse(
            'pootle-user-profile',
            kwargs=dict(username=member.username)))
    assert isinstance(response.context["view"], UserDetailView)
    profile = response.context["profile"]
    assert isinstance(profile, UserProfile)
    assert profile.user == member
