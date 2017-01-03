# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.utils.translation import get_language
from django.urls import reverse

from pootle.core.delegate import revision
from pootle_app.views.index.index import WelcomeView
from pootle_score.display import TopScoreDisplay


@pytest.mark.django_db
def test_view_welcome(client, member, system, project_set):
    response = client.get(reverse('pootle-home'))
    assert isinstance(response.context["top_scorers"], TopScoreDisplay)
    assert isinstance(response.context["view"], WelcomeView)
    assert response.context["view"].request_lang == get_language()
    assert (
        response.context["view"].project_set.directory
        == project_set.directory)
    assert (
        response.context["view"].revision
        == revision.get(project_set.directory.__class__)(
            project_set.directory).get(key="stats"))
    assert (
        response.context["view"].cache_key
        == (
            "%s.%s.%s"
            % (response.wsgi_request.user.username,
               response.context["view"].revision,
               get_language())))
