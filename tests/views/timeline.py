# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from hashlib import md5
import json

import pytest

from django.template import loader
from django.urls import reverse
from django.utils.encoding import force_bytes

from pootle.core.delegate import grouped_events, review
from pootle_comment.forms import UnsecuredCommentForm
from pootle_store.constants import (
    FUZZY, OBSOLETE, TRANSLATED, UNTRANSLATED)
from pootle_store.models import (
    Suggestion, QualityCheck, Unit)
from pootle_store.unit.timeline import EventGroup, UnitTimelineLog


class ProxyTimelineLanguage(object):

    def __init__(self, code):
        self.code = code


class ProxyTimelineUser(object):

    def __init__(self, submission):
        self.submission = submission

    @property
    def username(self):
        return self.submission["submitter__username"]

    @property
    def email_hash(self):
        return md5(force_bytes(self.submission['submitter__email'])).hexdigest()

    @property
    def display_name(self):
        return (
            self.submission["submitter__full_name"].strip()
            if self.submission["submitter__full_name"].strip()
            else self.submission["submitter__username"])


def _calculate_timeline(request, unit):
    groups = []
    log = UnitTimelineLog(unit)
    grouped_events_class = grouped_events.get(log.__class__)
    target_event = None
    for _key, group in grouped_events_class(log).grouped_events():
        event_group = EventGroup(group, target_event)
        if event_group.target_event:
            target_event = event_group.target_event
        if event_group.events:
            groups.append(event_group.context)

    context = dict(event_groups=groups)
    context.setdefault(
        'language', ProxyTimelineLanguage(
            unit.store.translation_project.language.code))
    t = loader.get_template('editor/units/xhr_timeline.html')
    return t.render(context=context, request=request)


def _timeline_test(client, request_user, unit):
    url = reverse("pootle-xhr-units-timeline", kwargs=dict(uid=unit.id))

    user = request_user["user"]
    if user.username != "nobody":
        client.login(
            username=user.username,
            password=request_user["password"])
    response = client.get(
        url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

    no_permission = (
        unit not in Unit.objects.get_translatable(user))

    if no_permission:
        assert response.status_code == 404
        assert "timeline" not in response
        return

    request = response.wsgi_request
    result = json.loads(response.content)
    assert result["uid"] == unit.id
    assert result["timeline"] == _calculate_timeline(request, unit)


@pytest.mark.django_db
def test_timeline_view_units(client, request_users, system, admin):
    _timeline_test(
        client,
        request_users,
        Unit.objects.filter(state=TRANSLATED).first())
    _timeline_test(
        client,
        request_users,
        Unit.objects.filter(state=UNTRANSLATED).first())


@pytest.mark.django_db
def test_timeline_view_unit_obsolete(client, request_users, system, admin):
    _timeline_test(
        client,
        request_users,
        Unit.objects.filter(state=OBSOLETE).first())


@pytest.mark.django_db
def test_timeline_view_unit_disabled_project(client, request_users,
                                             system, admin):
    unit = Unit.objects.filter(
        store__translation_project__project__disabled=True,
        store__obsolete=False,
        state=TRANSLATED).first()
    _timeline_test(
        client,
        request_users,
        unit)


@pytest.mark.django_db
def test_timeline_view_unit_with_suggestion(client, request_users,
                                            system, admin, store0):
    # test with "state change" subission - apparently this is what is required
    # to get one
    suggestion = Suggestion.objects.filter(
        unit__store=store0,
        state__name="pending",
        unit__state=UNTRANSLATED).first()
    unit = suggestion.unit
    unit.state = FUZZY
    unit.save()
    review.get(Suggestion)([suggestion], admin).accept()
    _timeline_test(
        client,
        request_users,
        unit)


@pytest.mark.django_db
def test_timeline_view_unit_with_qc(client, request_users, system, admin, store0):
    # check a Unit with a quality check
    qc_filter = dict(
        unit__store=store0,
        unit__state=TRANSLATED,
        unit__store__translation_project__project__disabled=False,
        unit__store__obsolete=False)
    qc = QualityCheck.objects.filter(**qc_filter).first()
    unit = qc.unit
    unit.toggle_qualitycheck(qc.id, True, admin)
    _timeline_test(
        client,
        request_users,
        unit)


@pytest.mark.django_db
def test_timeline_view_unit_with_suggestion_and_comment(client, request_users,
                                                        system, admin, store0):
    # test with "state change" subission - apparently this is what is required
    # to get one
    suggestion = Suggestion.objects.filter(
        unit__store=store0,
        state__name="pending",
        unit__state=UNTRANSLATED).first()
    unit = suggestion.unit
    unit.state = FUZZY
    unit.save()
    review.get(Suggestion)([suggestion], admin).accept()
    form = UnsecuredCommentForm(suggestion, dict(
        comment='This is a comment!',
        user=admin,
    ))
    if form.is_valid():
        form.save()

    _timeline_test(
        client,
        request_users,
        unit)


@pytest.mark.django_db
def test_timeline_view_unit_with_creation(client, request_users,
                                          system, admin, store0):
    # add a creation submission for a unit and test with that
    unit = Unit.objects.create(
        state=TRANSLATED, source_f="Foo", target_f="Bar",
        store=store0)
    # save and get the unit to deal with mysql's microsecond issues
    unit.save()
    unit = Unit.objects.get(pk=unit.pk)
    _timeline_test(
        client,
        request_users,
        unit)
