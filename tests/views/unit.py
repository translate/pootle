# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.http import Http404

from pytest_pootle.utils import create_api_request

from pootle.core.exceptions import Http400
from pootle_app.models.permissions import check_permission
from pootle_comment import get_model as get_comment_model
from pootle_store.models import Suggestion, Unit, UNTRANSLATED
from pootle_store.views import get_units


@pytest.mark.django_db
def test_get_units(rf, default):
    """Tests units can be retrieved."""
    view = get_units

    # `path` query parameter missing
    request = create_api_request(rf, user=default)
    with pytest.raises(Http400):
        view(request)

    # `path` query parameter present
    request = create_api_request(rf, url='/?path=foo', user=default)
    with pytest.raises(Http404):
        view(request)


@pytest.mark.django_db
def test_get_units_ordered(rf, default, admin, test_get_units_po):
    """Tests units can be retrieved while applying order filters."""
    view = get_units

    url = '/?path=/af/tutorial/&filter=incomplete&sort=newest&initial=true'

    request = create_api_request(rf, url=url, user=default)
    response = view(request)
    assert response.status_code == 200

    request = create_api_request(rf, url=url, user=admin)
    response = view(request)
    assert response.status_code == 200


@pytest.mark.django_db
def test_submit_with_suggestion_and_comment(client, request_users, settings):
    """Tests translation can be applied after suggestion is accepted."""
    settings.POOTLE_CAPTCHA_ENABLED = False
    Comment = get_comment_model()
    unit = Unit.objects.filter(suggestion__state='pending',
                               state=UNTRANSLATED)[0]
    sugg = Suggestion.objects.filter(unit=unit, state='pending')[0]
    user = request_users["user"]
    if user.username != "nobody":
        client.login(
            username=user.username,
            password=request_users["password"])

    url = '/xhr/units/%d/' % unit.id
    edited_target = "Edited %s" % sugg.target_f
    comment = 'This is a comment!'

    response = client.post(
        url,
        {
            'state': False,
            'target_f_0': edited_target,
            'suggestion': sugg.id,
            'comment': comment
        },
        HTTP_X_REQUESTED_WITH='XMLHttpRequest'
    )

    if check_permission('translate', response.wsgi_request):
        assert response.status_code == 200
        accepted_suggestion = Suggestion.objects.get(id=sugg.id)
        updated_unit = Unit.objects.get(id=unit.id)

        assert accepted_suggestion.state == 'accepted'
        assert str(updated_unit.target) == edited_target
        assert (Comment.objects
                       .for_model(accepted_suggestion)
                       .get().comment == comment)
    else:
        assert response.status_code == 403


@pytest.mark.django_db
def test_accept_suggestion_with_comment(client, request_users, settings):
    """Tests suggestion can be accepted with a comment."""
    settings.POOTLE_CAPTCHA_ENABLED = False
    Comment = get_comment_model()
    unit = Unit.objects.filter(suggestion__state='pending',
                               state=UNTRANSLATED)[0]
    sugg = Suggestion.objects.filter(unit=unit, state='pending')[0]
    user = request_users["user"]
    if user.username != "nobody":
        client.login(
            username=user.username,
            password=request_users["password"])

    url = '/xhr/units/%d/suggestions/%d/' % (unit.id, sugg.id)
    comment = 'This is a comment!'
    response = client.post(
        url,
        {
            'comment': comment
        },
        HTTP_X_REQUESTED_WITH='XMLHttpRequest'
    )

    if check_permission('review', response.wsgi_request):
        assert response.status_code == 200
        accepted_suggestion = Suggestion.objects.get(id=sugg.id)
        updated_unit = Unit.objects.get(id=unit.id)

        assert accepted_suggestion.state == 'accepted'
        assert str(updated_unit.target) == str(sugg.target)
        assert (Comment.objects
                       .for_model(accepted_suggestion)
                       .get().comment == comment)
    else:
        assert response.status_code == 403


@pytest.mark.django_db
def test_reject_suggestion_with_comment(client, request_users):
    """Tests suggestion can be rejected with a comment."""
    Comment = get_comment_model()
    unit = Unit.objects.filter(suggestion__state='pending',
                               state=UNTRANSLATED)[0]
    sugg = Suggestion.objects.filter(unit=unit, state='pending')[0]
    comment = 'This is a comment!'
    user = request_users["user"]
    if user.username != "nobody":
        client.login(
            username=user.username,
            password=request_users["password"])

    url = '/xhr/units/%d/suggestions/%d/' % (unit.id, sugg.id)
    response = client.delete(
        url,
        'comment=%s' % comment,
        HTTP_X_REQUESTED_WITH='XMLHttpRequest'
    )

    can_reject = (
        check_permission('review', response.wsgi_request)
        or sugg.user.id == user.id
    )
    if can_reject:
        assert response.status_code == 200
        rejected_suggestion = Suggestion.objects.get(id=sugg.id)

        assert rejected_suggestion.state == 'rejected'
        assert (Comment.objects
                       .for_model(rejected_suggestion)
                       .get().comment == comment)
    else:
        assert response.status_code == 403
