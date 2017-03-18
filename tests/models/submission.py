# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.utils import timezone

from pytest_pootle.utils import create_store

from pootle_app.models.permissions import check_permission
from pootle_statistics.models import (Submission, SubmissionFields,
                                      SubmissionTypes)
from pootle_store.constants import UNTRANSLATED
from pootle_store.models import Suggestion, Unit


def _create_comment_submission(unit, user, creation_time, comment):
    sub = Submission(
        creation_time=creation_time,
        translation_project=unit.store.translation_project,
        submitter=user,
        unit=unit,
        field=SubmissionFields.COMMENT,
        type=SubmissionTypes.WEB,
        new_value=comment,
    )
    sub.save()
    return sub


@pytest.mark.django_db
def test_submission_ordering(store0, member):
    """Submissions with same creation_time should order by pk
    """

    at_time = timezone.now()
    unit = store0.units[0]

    last_sub_pk = unit.submission_set.order_by(
        "-pk").values_list("pk", flat=True).first() or 0
    _create_comment_submission(unit, member, at_time, "Comment 3")
    _create_comment_submission(unit, member, at_time, "Comment 2")
    _create_comment_submission(unit, member, at_time, "Comment 1")
    new_subs = unit.submission_set.filter(pk__gt=last_sub_pk)

    # Object manager test
    assert new_subs.count() == 3
    assert (new_subs.first().creation_time
            == new_subs.last().creation_time)
    assert (new_subs.latest().pk
            > new_subs.earliest().pk)

    # Passing field_name test
    assert (new_subs.earliest("new_value").new_value
            == "Comment 1")
    assert (new_subs.latest("new_value").new_value
            == "Comment 3")
    assert (new_subs.earliest("pk").new_value
            == "Comment 3")
    assert (new_subs.latest("pk").new_value
            == "Comment 1")


@pytest.mark.django_db
def test_update_submission_ordering():
    unit = Unit.objects.filter(state=UNTRANSLATED).first()
    unit.markfuzzy()
    unit.target = "Fuzzy Translation for " + unit.source_f
    unit.save()

    store = create_store(
        unit.store.pootle_path,
        "0",
        [(unit.source_f, "Translation for " + unit.source_f, False)]
    )
    unit.store.update(store)
    submission_field = Submission.objects.filter(unit=unit).latest().field
    assert submission_field == SubmissionFields.STATE


@pytest.mark.django_db
def test_new_translation_submission_ordering(client, request_users, settings):
    unit = Unit.objects.filter(state=UNTRANSLATED).first()
    settings.POOTLE_CAPTCHA_ENABLED = False
    user = request_users["user"]
    if user.username != "nobody":
        client.login(
            username=user.username,
            password=request_users["password"])
    url = '/xhr/units/%d/' % unit.id
    response = client.post(
        url,
        {'is_fuzzy': "0",
         'target_f_0': "Translation for " + unit.source_f},
        HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    if check_permission('translate', response.wsgi_request):
        assert response.status_code == 200
        submission_field = Submission.objects.filter(unit=unit).latest().field
        assert submission_field == SubmissionFields.STATE
    else:
        assert response.status_code == 403


@pytest.mark.django_db
def test_accept_sugg_submission_ordering(client, request_users, settings):
    """Tests suggestion can be accepted with a comment."""
    settings.POOTLE_CAPTCHA_ENABLED = False
    unit = Unit.objects.filter(suggestion__state__name='pending',
                               state=UNTRANSLATED)[0]
    unit.markfuzzy()
    unit.target = "Fuzzy Translation for " + unit.source_f
    unit.save()
    sugg = Suggestion.objects.filter(unit=unit, state__name='pending')[0]
    user = request_users["user"]
    last_sub_pk = unit.submission_set.order_by(
        "-pk").values_list("pk", flat=True).first() or 0
    if user.username != "nobody":
        client.login(
            username=user.username,
            password=request_users["password"])

    url = '/xhr/units/%d/suggestions/%d/' % (unit.id, sugg.id)
    response = client.post(
        url,
        HTTP_X_REQUESTED_WITH='XMLHttpRequest'
    )
    new_subs = unit.submission_set.filter(pk__gt=last_sub_pk)
    if check_permission('review', response.wsgi_request):
        assert response.status_code == 200
        assert new_subs.count() == 2
        target_sub = new_subs.order_by("pk").first()
        assert target_sub.field == SubmissionFields.TARGET
        state_sub = new_subs.order_by("pk").last()
        assert state_sub.field == SubmissionFields.STATE
    else:
        assert response.status_code == 404
        assert new_subs.count() == 0
