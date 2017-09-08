# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle_app.forms import PermissionsUsersSearchForm
from pootle_app.models.permissions import PermissionSet, get_pootle_permission


@pytest.mark.django_db
def test_form_permissions_users(project0, member, member2):

    # must supply a directory
    with pytest.raises(KeyError):
        PermissionsUsersSearchForm()

    form = PermissionsUsersSearchForm(
        directory=project0.directory, data={})

    assert not form.is_valid()
    assert "q" in form.errors

    form = PermissionsUsersSearchForm(
        directory=project0.directory,
        data=dict(q="mem"))

    assert form.is_valid()
    assert form.cleaned_data == dict(q="mem")
    results = form.search()["results"]
    assert results[0]['text'] == member.username
    assert results[0]['id'] == member.pk
    assert results[1]['text'] == member2.username
    assert results[1]['id'] == member2.pk

    # providing a user with permissions in this directory
    # means they are excluded from search results
    view = get_pootle_permission('view')
    perm_set = PermissionSet.objects.create(
        user=member,
        directory=project0.directory)
    perm_set.positive_permissions.add(view)
    assert form.search() == {
        'results': [
            {'text': member2.username, 'id': member2.pk}]}
