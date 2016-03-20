# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from hashlib import md5
from itertools import groupby
import json

import pytest

from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.template import RequestContext, loader
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from pootle_misc.checks import check_names
from pootle_statistics.models import (
    Submission, SubmissionFields, SubmissionTypes)
from pootle_store.fields import to_python
from pootle_store.models import (
    FUZZY, OBSOLETE, TRANSLATED, UNTRANSLATED,
    Suggestion, SuggestionStates, QualityCheck, Store, Unit)
from pootle_store.util import STATES_MAP


class ProxyTimelineLanguage(object):

    def __init__(self, code):
        self.code = code


class ProxyTimelineUser(object):

    def __init__(self, submission):
        self.submission = submission

    @property
    def display_name(self):
        return (
            self.submission["submitter__full_name"].strip()
            if self.submission["submitter__full_name"].strip()
            else self.submission["submitter__username"])

    def get_absolute_url(self):
        return reverse(
            'pootle-user-profile',
            args=[self.submission["submitter__username"]])

    def gravatar_url(self, size=80):
        email_hash = md5(self.submission['submitter__email']).hexdigest()
        return (
            'https://secure.gravatar.com/avatar/%s?s=%d&d=mm'
            % (email_hash, size))


def _get_suggestion_description(submission):
    user_url = reverse(
        'pootle-user-profile',
        args=[submission["suggestion__user__username"]])
    display_name = (
        submission["suggestion__user__full_name"].strip()
        if submission["suggestion__user__full_name"].strip()
        else submission["suggestion__user__username"])
    author = format_html(u'<a href="{}">{}</a>', user_url, display_name)
    return {
        SubmissionTypes.SUGG_ADD: _(u'Added suggestion'),
        SubmissionTypes.SUGG_ACCEPT: _(u'Accepted suggestion from %s',
                                       author),
        SubmissionTypes.SUGG_REJECT: _(u'Rejected suggestion from %s',
                                       author)}.get(submission['type'], None)


def _calculate_timeline(request, unit):
    submission_filter = (
        Q(field__in=[SubmissionFields.TARGET, SubmissionFields.STATE,
                     SubmissionFields.COMMENT, SubmissionFields.NONE])
        | Q(type__in=SubmissionTypes.SUGGESTION_TYPES))
    timeline = (
        Submission.objects.filter(unit=unit)
                          .filter(submission_filter)
                          .exclude(field=SubmissionFields.COMMENT,
                                   creation_time=unit.commented_on)
                          .order_by("id"))
    User = get_user_model()
    entries_group = []
    context = {}
    timeline_fields = [
        "type", "old_value", "new_value", "submitter_id", "creation_time",
        "translation_project__language__code", "field", "suggestion_id",
        "suggestion__target_f", "quality_check__name", "submitter__username",
        "submitter__full_name", "suggestion__user__full_name", "submitter__email",
        "suggestion__user__username"]

    grouped_timeline = groupby(
        timeline.values(*timeline_fields),
        key=lambda x: ("%d\001%s" % (x['submitter_id'], x['creation_time'])))

    # Group by submitter id and creation_time because
    # different submissions can have same creation time
    for key, values in grouped_timeline:
        entry_group = {
            'entries': [],
        }

        for item in values:
            # Only add creation_time information for the whole entry group once
            entry_group['datetime'] = item['creation_time']

            # Only add submitter information for the whole entry group once
            entry_group.setdefault('submitter', ProxyTimelineUser(item))

            context.setdefault(
                'language',
                ProxyTimelineLanguage(item['translation_project__language__code']))

            entry = {
                'field': item['field'],
                'field_name': SubmissionFields.NAMES_MAP.get(item['field'], None),
                'type': item['type']}
            if item['field'] == SubmissionFields.STATE:
                entry['old_value'] = STATES_MAP[int(to_python(item['old_value']))]
                entry['new_value'] = STATES_MAP[int(to_python(item['new_value']))]
            elif item['suggestion_id']:
                entry.update({
                    'suggestion_text': item['suggestion__target_f'],
                    'suggestion_description':
                        mark_safe(_get_suggestion_description(item))})
            elif item['quality_check__name']:
                check_name = item['quality_check__name']
                check_url = (
                    u''.join(
                        [reverse('pootle-checks-descriptions'),
                         '#', check_name]))
                entry.update({
                    'check_name': check_name,
                    'check_display_name': check_names[check_name],
                    'checks_url': check_url})
            else:
                entry['new_value'] = to_python(item['new_value'])

            entry_group['entries'].append(entry)

        entries_group.append(entry_group)

    has_creation_entry = (
        len(entries_group) > 0
        and entries_group[0]['datetime'] == unit.creation_time)
    if (has_creation_entry):
        entries_group[0]['created'] = True
    else:
        created = {
            'created': True,
            'submitter': User.objects.get_system_user()}

        if unit.creation_time:
            created['datetime'] = unit.creation_time
        entries_group[:0] = [created]

    # Let's reverse the chronological order
    entries_group.reverse()
    context['entries_group'] = entries_group
    t = loader.get_template('editor/units/xhr_timeline.html')
    c = RequestContext(request, context)
    return t.render(c).replace('\n', '')


def _timeline_test(client, request_user, unit):
    url = reverse("pootle-xhr-units-timeline", kwargs=dict(uid=unit.id))

    user = request_user["user"]
    if user.username != "nobody":
        client.login(
            username=user.username,
            password=request_user["password"])
    response = client.get(url)

    no_permission = (
        not user.is_superuser
        and unit not in Unit.objects.get_translatable(user))

    if no_permission:
        assert response.status_code == 403
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


@pytest.mark.xfail(
    reason="timeline does not currently check permissions correctly")
@pytest.mark.django_db
def test_timeline_view_unit_obsolete(client, request_users, system, admin):
    _timeline_test(
        client,
        request_users,
        Unit.objects.filter(state=OBSOLETE).first())


@pytest.mark.xfail(
    reason="timeline does not currently check permissions correctly")
@pytest.mark.django_db
def test_timeline_view_unit_disabled_project(client, request_users,
                                             system, admin):
    unit = Unit.objects.filter(
        store__translation_project__project__disabled=True,
        state=TRANSLATED).first()
    _timeline_test(
        client,
        request_users,
        unit)


@pytest.mark.django_db
def test_timeline_view_unit_with_suggestion(client, request_users,
                                            system, admin):
    # test with "state change" subission - apparently this is what is required
    # to get one
    suggestion = Suggestion.objects.filter(
        state=SuggestionStates.PENDING,
        unit__state=UNTRANSLATED).first()
    unit = suggestion.unit
    unit.state = FUZZY
    unit.save()
    unit.accept_suggestion(suggestion, unit.store.translation_project, admin)
    _timeline_test(
        client,
        request_users,
        unit)


@pytest.mark.django_db
def test_timeline_view_unit_with_qc(client, request_users, system, admin):
    # check a Unit with a quality check
    qc_filter = dict(
        unit__state=TRANSLATED,
        unit__store__translation_project__project__disabled=False)
    qc = QualityCheck.objects.filter(**qc_filter).first()
    unit = qc.unit
    unit.toggle_qualitycheck(qc.id, True, admin)
    _timeline_test(
        client,
        request_users,
        unit)


@pytest.mark.django_db
def test_timeline_view_unit_with_creation(client, request_users,
                                          system, admin):
    # add a creation submission for a unit and test with that
    store = Store.objects.exclude(
        translation_project__project__disabled=True).first()
    index = max(store.unit_set.values_list("index", flat=True)) + 1
    unit = Unit.objects.create(
        state=TRANSLATED, source_f="Foo", target_f="Bar",
        store=store, index=index)
    # save and get the unit to deal with mysql's microsecond issues
    unit.save()
    unit = Unit.objects.get(pk=unit.pk)
    unit.add_initial_submission(system)
    _timeline_test(
        client,
        request_users,
        unit)
