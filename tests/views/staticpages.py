# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from __future__ import absolute_import

import pytest

from pytest_pootle.fixtures.models.permission_set import _require_permission_set

from pootle_app.models.permissions import check_user_permission
from pootle_translationproject.models import TranslationProject

from staticpages.models import StaticPage


@pytest.mark.django_db
def test_edit_announcement(administrate, client, request_users, settings):
    settings.POOTLE_CAPTCHA_ENABLED = False
    tp = TranslationProject.objects.first()
    user = request_users["user"]
    if user.username == "member2":
        _require_permission_set(user, tp.directory, [administrate])

    ann = StaticPage.get_announcement_for(tp.pootle_path)
    if user.username != "nobody":
        client.login(
            username=user.username,
            password=request_users["password"],
        )

    url = "/xhr/announcement/%d/edit/" % ann.pk
    response = client.post(
        url,
        {
            'title': ann.title,
            'active': True,
            'virtual_path': ann.virtual_path,
            'body': "Changed announcement"
        },
        HTTP_X_REQUESTED_WITH='XMLHttpRequest',
    )
    if check_user_permission(user, "administrate", tp.directory):
        assert response.status_code == 200
        ann = StaticPage.get_announcement_for(tp.pootle_path)
        assert ann.body.raw == "Changed announcement"
    else:
        assert response.status_code == 400
