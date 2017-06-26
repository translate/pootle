# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import json
import pytest

from django.http import Http404, QueryDict

from pytest_pootle.utils import create_api_request

from translate.misc.multistring import multistring

from pootle.core.exceptions import Http400
from pootle_app.models.permissions import check_permission
from pootle_comment import get_model as get_comment_model
from pootle_statistics.models import SubmissionFields, SubmissionTypes
from pootle_store.constants import FUZZY, TRANSLATED, UNTRANSLATED
from pootle_store.models import QualityCheck, Suggestion, Unit, UnitChange
from pootle_store.views import get_units, toggle_qualitycheck


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
def test_get_units_ordered(rf, default, admin, numbered_po):
    """Tests units can be retrieved while applying order filters."""
    view = get_units
    tp = numbered_po.translation_project
    url = (
        '/?path=/%s/%s/&filter=incomplete&sort=newest&initial=true'
        % (tp.language.code, tp.project.code))

    request = create_api_request(rf, url=url, user=default)
    response = view(request)
    assert response.status_code == 200

    request = create_api_request(rf, url=url, user=admin)
    response = view(request)
    assert response.status_code == 200


@pytest.mark.django_db
def test_submit_with_suggestion_and_comment(client, request_users,
                                            settings, system):
    """Tests translation can be applied after suggestion is accepted."""
    settings.POOTLE_CAPTCHA_ENABLED = False
    Comment = get_comment_model()
    unit = Unit.objects.filter(
        suggestion__state__name='pending',
        state=UNTRANSLATED)[0]
    last_sub_pk = unit.submission_set.order_by(
        "id").values_list("id", flat=True).last() or 0
    sugg = Suggestion.objects.filter(unit=unit, state__name='pending')[0]
    user = request_users["user"]

    if user.username != "nobody":
        client.login(
            username=user.username,
            password=request_users["password"])

    url = '/xhr/units/%d/' % unit.id
    edited_target = "Edited %s" % sugg.target_f
    comment = 'This is a comment!'
    qdict = QueryDict(mutable=True)
    qdict.update(
        {'state': False,
         'target_f_0': edited_target,
         'suggestion': sugg.id,
         'comment': comment})
    qdict._mutable = False
    response = client.post(
        url,
        qdict,
        HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    suggestion = Suggestion.objects.get(id=sugg.id)
    unit = Unit.objects.get(id=unit.id)
    new_subs = unit.submission_set.filter(id__gt=last_sub_pk).order_by("id")
    if check_permission('translate', response.wsgi_request):
        assert response.status_code == 200
        content = json.loads(response.content)
        assert content['newtargets'] == [edited_target]
        assert content['user_score'] == response.wsgi_request.user.public_score
        assert content['checks'] is None
        unit_source = unit.unit_source
        assert unit_source.created_by == system
        assert unit_source.created_with == SubmissionTypes.SYSTEM
        assert unit.change.submitted_by == suggestion.user
        if user == suggestion.user:
            assert unit.change.reviewed_by is None
            assert unit.change.reviewed_on is None
        else:
            assert unit.change.reviewed_by == user
            assert unit.change.reviewed_on == unit.mtime
        assert unit.change.changed_with == SubmissionTypes.WEB

        assert suggestion.state.name == 'accepted'
        assert suggestion.is_accepted
        assert str(unit.target) == edited_target
        assert (Comment.objects
                       .for_model(suggestion)
                       .get().comment == comment)
        assert new_subs.count() == 2
        target_sub = new_subs[0]
        assert target_sub.old_value == ""
        assert target_sub.new_value == unit.target
        assert target_sub.field == SubmissionFields.TARGET
        assert target_sub.type == SubmissionTypes.WEB
        assert target_sub.submitter == unit.change.submitted_by
        assert target_sub.suggestion == suggestion
        assert target_sub.revision == unit.revision
        assert target_sub.creation_time == unit.mtime

        state_sub = new_subs[1]
        assert state_sub.old_value == str(UNTRANSLATED)
        assert state_sub.new_value == str(unit.state)
        assert state_sub.suggestion == suggestion

        assert state_sub.field == SubmissionFields.STATE
        assert state_sub.type == SubmissionTypes.WEB

        assert state_sub.submitter == unit.change.submitted_by
        assert state_sub.revision == unit.revision
        assert state_sub.creation_time == unit.mtime
    else:
        assert response.status_code == 403
        assert suggestion.state.name == "pending"
        assert suggestion.is_pending
        assert unit.target == ""
        assert new_subs.count() == 0
        with pytest.raises(UnitChange.DoesNotExist):
            unit.change


@pytest.mark.django_db
def test_submit_with_suggestion(client, request_users, settings, system):
    """Tests translation can be applied after suggestion is accepted."""
    settings.POOTLE_CAPTCHA_ENABLED = False
    unit = Unit.objects.filter(suggestion__state__name='pending',
                               state=UNTRANSLATED).first()
    last_sub_pk = unit.submission_set.order_by(
        "-pk").values_list("pk", flat=True).first() or 0
    sugg = Suggestion.objects.filter(unit=unit, state__name='pending').first()
    user = request_users["user"]
    if user.username != "nobody":
        client.login(
            username=user.username,
            password=request_users["password"])

    url = '/xhr/units/%d/' % unit.id

    response = client.post(
        url,
        {
            'state': False,
            'target_f_0': sugg.target_f,
            'suggestion': sugg.id,
        },
        HTTP_X_REQUESTED_WITH='XMLHttpRequest'
    )

    suggestion = Suggestion.objects.get(id=sugg.id)
    unit = Unit.objects.get(id=unit.id)
    new_subs = unit.submission_set.filter(id__gt=last_sub_pk)
    if check_permission('translate', response.wsgi_request):
        assert response.status_code == 200
        unit_source = unit.unit_source
        assert unit_source.created_by == system
        assert unit_source.created_with == SubmissionTypes.SYSTEM
        assert unit.change.submitted_by == suggestion.user
        if user == suggestion.user:
            assert unit.change.reviewed_by is None
        else:
            assert unit.change.reviewed_by == user
        assert unit.change.changed_with == SubmissionTypes.WEB
        assert suggestion.state.name == 'accepted'
        assert suggestion.is_accepted
        assert str(unit.target) == sugg.target_f
        assert new_subs.count() == 2
        target_sub = new_subs[0]
        assert target_sub.suggestion == suggestion
        assert target_sub.field == SubmissionFields.TARGET
        assert target_sub.type == SubmissionTypes.WEB
        assert target_sub.submitter == suggestion.user

        state_sub = new_subs[1]
        assert state_sub.suggestion == suggestion
        assert state_sub.field == SubmissionFields.STATE
        assert state_sub.type == SubmissionTypes.WEB
        assert state_sub.submitter == suggestion.user
    else:
        assert response.status_code == 403
        assert new_subs.count() == 0
        assert suggestion.state.name == "pending"
        assert suggestion.is_pending
        assert unit.target == ""
        with pytest.raises(UnitChange.DoesNotExist):
            unit.change


@pytest.mark.django_db
def test_accept_suggestion_with_comment(client, request_users, settings, system):
    """Tests suggestion can be accepted with a comment."""
    settings.POOTLE_CAPTCHA_ENABLED = False
    Comment = get_comment_model()
    unit = Unit.objects.filter(suggestion__state__name='pending',
                               state=UNTRANSLATED)[0]
    sugg = Suggestion.objects.filter(unit=unit, state__name='pending')[0]
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

    suggestion = Suggestion.objects.get(id=sugg.id)
    unit = Unit.objects.get(id=unit.id)
    if check_permission('review', response.wsgi_request):
        assert response.status_code == 200
        unit_source = unit.unit_source
        assert unit_source.created_by == system
        assert unit_source.created_with == SubmissionTypes.SYSTEM
        assert unit.change.submitted_by == suggestion.user
        assert unit.change.reviewed_by == user
        assert unit.change.changed_with == SubmissionTypes.WEB
        assert suggestion.state.name == 'accepted'
        assert suggestion.is_accepted
        assert str(unit.target) == str(suggestion.target)
        assert (Comment.objects
                       .for_model(suggestion)
                       .get().comment == comment)
    else:
        assert response.status_code == 404
        assert suggestion.state.name == "pending"
        assert suggestion.is_pending
        assert unit.target == ""
        with pytest.raises(UnitChange.DoesNotExist):
            unit.change


@pytest.mark.django_db
def test_reject_suggestion_with_comment(client, request_users):
    """Tests suggestion can be rejected with a comment."""
    Comment = get_comment_model()
    unit = Unit.objects.filter(suggestion__state__name='pending',
                               state=UNTRANSLATED)[0]
    sugg = Suggestion.objects.filter(unit=unit, state__name='pending')[0]
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
    suggestion = Suggestion.objects.get(id=sugg.id)
    if can_reject:
        assert response.status_code == 200
        assert suggestion.state.name == 'rejected'
        assert suggestion.is_rejected
        assert unit.target == ""
        # unit is untranslated so no change
        with pytest.raises(UnitChange.DoesNotExist):
            unit.change
        assert (Comment.objects
                       .for_model(suggestion)
                       .get().comment == comment)
    else:
        assert response.status_code == 404
        assert unit.target == ""
        assert suggestion.state.name == "pending"
        assert suggestion.is_pending
        with pytest.raises(UnitChange.DoesNotExist):
            unit.change


@pytest.mark.django_db
def test_non_pending_suggestion(client, request_users, member, system):
    unit = Unit.objects.filter(
        suggestion__state__name='accepted')[0]
    unit.target = "EXISTING TARGET"
    unit.save(
        user=member,
        changed_with=SubmissionTypes.UPLOAD)
    suggestion = Suggestion.objects.filter(
        unit=unit,
        state__name='accepted')[0]
    user = request_users["user"]
    if user.username != "nobody":
        client.login(
            username=user.username,
            password=request_users["password"])
    url = (
        '/xhr/units/%d/suggestions/%d/'
        % (unit.id, suggestion.id))
    response = client.delete(
        url,
        HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    can_review = (
        check_permission('review', response.wsgi_request)
        or suggestion.user.id == user.id)
    if can_review:
        assert response.status_code == 400
    else:
        assert response.status_code == 404


@pytest.mark.django_db
def test_reject_translated_suggestion(client, request_users, member, system):
    """Tests suggestion can be rejected with a comment."""
    unit = Unit.objects.filter(
        suggestion__state__name='pending',
        state=UNTRANSLATED)[0]
    unit.target = "EXISTING TARGET"
    unit.save(
        user=member,
        changed_with=SubmissionTypes.UPLOAD)
    suggestion = Suggestion.objects.filter(
        unit=unit,
        state__name='pending')[0]
    user = request_users["user"]
    if user.username != "nobody":
        client.login(
            username=user.username,
            password=request_users["password"])
    url = (
        '/xhr/units/%d/suggestions/%d/'
        % (unit.id, suggestion.id))
    response = client.delete(
        url,
        HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    can_reject = (
        check_permission('review', response.wsgi_request)
        or suggestion.user.id == user.id)
    unit.refresh_from_db()
    unit.change.refresh_from_db()
    unit_source = unit.unit_source
    suggestion.refresh_from_db()
    if can_reject:
        assert response.status_code == 200
        assert suggestion.state.name == 'rejected'
        assert suggestion.is_rejected
        assert unit_source.created_by == system
        assert unit.change.changed_with == SubmissionTypes.UPLOAD
        assert unit.change.submitted_by == member
        assert unit.change.reviewed_by == user
    else:
        assert response.status_code == 404
        assert unit.target == "EXISTING TARGET"
        assert suggestion.state.name == "pending"
        assert suggestion.is_pending


@pytest.mark.django_db
def test_toggle_quality_check(rf, admin, member):
    """Tests the view that mutes/unmutes quality checks."""
    qc_filter = dict(
        false_positive=False,
        unit__state=TRANSLATED,
        unit__store__translation_project__project__disabled=False,
    )
    qc = QualityCheck.objects.filter(**qc_filter).first()
    unit = qc.unit

    unit.change.reviewed_by = member
    unit.change.save()
    # Explicit POST data present, mute
    data = 'mute='
    request = create_api_request(rf, method='post', user=admin, data=data,
                                 encode_as_json=False)
    response = toggle_qualitycheck(request, unit.id, qc.id)
    assert response.status_code == 200
    assert QualityCheck.objects.get(id=qc.id).false_positive is True
    sub = unit.submission_set.get(quality_check=qc)
    assert sub.submitter == admin
    unit.change.refresh_from_db()
    assert unit.change.reviewed_by == admin

    unit.change.reviewed_by = member
    unit.change.save()
    # No POST data present, unmute
    request = create_api_request(rf, method='post', user=admin)
    response = toggle_qualitycheck(request, unit.id, qc.id)
    assert response.status_code == 200
    assert QualityCheck.objects.get(id=qc.id).false_positive is False
    sub = unit.submission_set.get(id__gt=sub.id, quality_check=qc)
    assert sub.submitter == admin
    unit.change.refresh_from_db()
    assert unit.change.reviewed_by == admin


@pytest.mark.django_db
def test_submit_unit_plural(client, unit_plural, request_users, settings):
    """Tests translation can be applied after suggestion is accepted."""
    settings.POOTLE_CAPTCHA_ENABLED = False
    user = request_users["user"]
    if user.username != "nobody":
        client.login(
            username=user.username,
            password=request_users["password"])

    url = '/xhr/units/%d/' % unit_plural.id
    original_target = unit_plural.target
    target = [
        "%s" % unit_plural.target.strings[0],
        "%s changed" % unit_plural.target.strings[1]
    ]
    response = client.post(
        url,
        {'target_f_0': target[0],
         'target_f_1': target[1],
         'is_fuzzy': "0"},
        HTTP_X_REQUESTED_WITH='XMLHttpRequest')

    unit = Unit.objects.get(id=unit_plural.id)
    if check_permission('translate', response.wsgi_request):
        assert response.status_code == 200
        assert unit.target == multistring(target)
    else:
        assert response.status_code == 403
        assert unit.target == original_target
        with pytest.raises(UnitChange.DoesNotExist):
            unit.change


@pytest.mark.django_db
def test_add_suggestion(client, request_users, settings):
    """Tests translation can be applied after suggestion is accepted."""
    settings.POOTLE_CAPTCHA_ENABLED = False
    user = request_users["user"]
    if user.username != "nobody":
        client.login(
            username=user.username,
            password=request_users["password"])

    unit = Unit.objects.all().first()
    url = '/xhr/units/%d/suggestions' % unit.id
    target = "%s TEST SUGGESTION" % unit.source
    response = client.post(
        url,
        {
            'target_f_0': target,
        },
        HTTP_X_REQUESTED_WITH='XMLHttpRequest'
    )

    assert response.status_code == 200
    changed = Unit.objects.get(id=unit.id)
    suggestion = changed.get_suggestions().order_by('id').last()
    assert suggestion.target == multistring(target)
    with pytest.raises(UnitChange.DoesNotExist):
        unit.change


@pytest.mark.django_db
def test_add_suggestion_same_as_target(client, request_users, settings):
    """Tests suggestion equal to target cannot be added."""
    settings.POOTLE_CAPTCHA_ENABLED = False
    user = request_users["user"]
    if user.username != "nobody":
        client.login(
            username=user.username,
            password=request_users["password"])

    unit = Unit.objects.filter(state=TRANSLATED).first()
    suggestion_count = unit.suggestion_set.count()
    url = '/xhr/units/%d/suggestions' % unit.id
    response = client.post(
        url,
        {
            'target_f_0': unit.target,
        },
        HTTP_X_REQUESTED_WITH='XMLHttpRequest'
    )

    assert response.status_code == 400
    assert suggestion_count == unit.suggestion_set.count()


@pytest.mark.django_db
def test_add_suggestion_same_as_pending(client, request_users, settings):
    """Tests suggestion equal to target cannot be added."""
    settings.POOTLE_CAPTCHA_ENABLED = False
    user = request_users["user"]
    if user.username != "nobody":
        client.login(
            username=user.username,
            password=request_users["password"])

    suggestion = Suggestion.objects.filter(state__name='pending').first()
    unit = suggestion.unit
    suggestion_count = unit.suggestion_set.count()
    url = '/xhr/units/%d/suggestions' % unit.id
    response = client.post(
        url,
        {
            'target_f_0': suggestion.target,
        },
        HTTP_X_REQUESTED_WITH='XMLHttpRequest'
    )

    assert response.status_code == 400
    assert suggestion_count == unit.suggestion_set.count()


@pytest.mark.django_db
def test_submit_unit(client, store0, request_users, settings, system):
    """Tests translation can be applied after suggestion is accepted."""
    settings.POOTLE_CAPTCHA_ENABLED = False
    user = request_users["user"]
    unit = store0.units.filter(state=UNTRANSLATED).first()
    if user.username != "nobody":
        client.login(
            username=user.username,
            password=request_users["password"])
    url = '/xhr/units/%d/' % unit.id
    old_target = unit.target
    response = client.post(
        url,
        dict(target_f_0=("%s changed" % unit.target),
             is_fuzzy="0",
             sfn="PTL.editor.processSubmission"),
        HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    unit.refresh_from_db()
    if user.username == "nobody":
        assert response.status_code == 403
        assert unit.target == ""
        with pytest.raises(UnitChange.DoesNotExist):
            unit.change
        return
    assert response.status_code == 200
    assert unit.target == "%s changed" % old_target
    assert unit.state == TRANSLATED
    unit.store.data.refresh_from_db()
    assert unit.store.data.last_submission.unit == unit
    unit_source = unit.unit_source
    unit.refresh_from_db()
    assert unit_source.created_by == system
    assert unit_source.created_with == SubmissionTypes.SYSTEM
    assert unit.change.changed_with == SubmissionTypes.WEB
    assert unit.change.submitted_by == user
    assert unit.change.reviewed_by is None


@pytest.mark.django_db
def test_submit_fuzzy_unit(client, store0, request_users, settings, system):
    """Test un/fuzzying units."""
    settings.POOTLE_CAPTCHA_ENABLED = False
    user = request_users["user"]
    unit = store0.units.filter(state=UNTRANSLATED).first()
    if user.username != "nobody":
        client.login(
            username=user.username,
            password=request_users["password"])
    url = '/xhr/units/%d/' % unit.id
    old_target = unit.target
    new_target = "%s changed" % unit.target
    response = client.post(
        url,
        dict(target_f_0=(new_target),
             is_fuzzy="1",
             sfn="PTL.editor.processSubmission"),
        HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    unit.refresh_from_db()
    if check_permission('translate', response.wsgi_request):
        assert response.status_code == 200
        assert unit.state == FUZZY
        assert unit.target == new_target
    else:
        assert response.status_code == 403
        assert unit.state == UNTRANSLATED
        assert unit.target == old_target
    response = client.post(
        url,
        dict(target_f_0=(new_target),
             is_fuzzy="0",
             sfn="PTL.editor.processSubmission"),
        HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    unit.refresh_from_db()
    if check_permission('translate', response.wsgi_request):
        assert response.status_code == 200
        assert unit.state == TRANSLATED
        assert unit.target == new_target
    else:
        assert response.status_code == 403
        assert unit.state == UNTRANSLATED
        assert unit.target == old_target
    # state is always untranslated if target is empty
    response = client.post(
        url,
        dict(target_f_0="",
             is_fuzzy="1",
             sfn="PTL.editor.processSubmission"),
        HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    unit.refresh_from_db()
    if check_permission('translate', response.wsgi_request):
        assert response.status_code == 200
        assert unit.target == ""
    else:
        assert response.status_code == 403
        assert unit.target == old_target
    assert unit.state == UNTRANSLATED
