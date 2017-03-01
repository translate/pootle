# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle_statistics.models import Submission
from pootle_statistics.proxy import SubmissionProxy


def _test_submission_proxy(proxy, sub, fields):
    assert proxy.field == sub.field
    if sub.field:
        assert proxy.field_name
    if sub.suggestion:
        assert proxy.suggestion == sub.suggestion.pk
        assert proxy.suggestion_target == sub.suggestion.target
    if sub.unit and "unit_id" in fields:
        assert proxy.unit == sub.unit.pk
        assert proxy.unit_source == sub.unit.source
        assert proxy.unit_translate_url == sub.unit.get_translate_url()
        assert proxy.unit_pootle_path == sub.unit.store.pootle_path
        assert proxy.unit_state == sub.unit.state
    assert proxy.type == sub.type
    if sub.quality_check:
        assert proxy.qc_name == sub.quality_check.name
    else:
        assert proxy.qc_name is None
    with pytest.raises(AttributeError):
        proxy.asdf


@pytest.mark.django_db
def test_submission_proxy_info(submissions):
    values = Submission.objects.values(
        *(("id", ) + SubmissionProxy.info_fields))
    for v in values.iterator():
        proxy = SubmissionProxy(v)
        submission = submissions[v["id"]]
        _test_submission_proxy(
            proxy,
            submission,
            SubmissionProxy.info_fields)
        assert (
            sorted(proxy.get_submission_info().items())
            == sorted(submission.get_submission_info().items()))


@pytest.mark.django_db
def test_submission_proxy_timeline(submissions):
    values = Submission.objects.values(
        *(("id", ) + SubmissionProxy.timeline_fields))
    for v in values.iterator():
        _test_submission_proxy(
            SubmissionProxy(v),
            submissions[v["id"]],
            SubmissionProxy.timeline_fields)


@pytest.mark.django_db
def test_submission_proxy_qc_timeline(quality_check_submission):
    subs = Submission.objects.filter(pk=quality_check_submission.pk)
    _test_submission_proxy(
        SubmissionProxy(
            subs.values(*SubmissionProxy.timeline_fields).first()),
        quality_check_submission,
        SubmissionProxy.timeline_fields)


@pytest.mark.django_db
def test_submission_proxy_qc_info(quality_check_submission):
    subs = Submission.objects.filter(pk=quality_check_submission.pk)
    proxy = SubmissionProxy(subs.values(*SubmissionProxy.info_fields).first())
    _test_submission_proxy(
        proxy,
        quality_check_submission,
        SubmissionProxy.info_fields)
    assert (
        sorted(proxy.get_submission_info().items())
        == sorted(quality_check_submission.get_submission_info().items()))


@pytest.mark.django_db
def test_submission_proxy_timeline_info(quality_check_submission):
    """If you use the timeline fields but call get_submission_info you will
    get the sub info without the unit data
    """
    subs = Submission.objects.filter(pk=quality_check_submission.pk)
    sub = subs.values(*SubmissionProxy.timeline_fields).first()
    proxy = SubmissionProxy(sub)
    assert proxy.unit_info == {}
    assert proxy.unit_translate_url is None
    assert proxy.unit_pootle_path is None
    assert proxy.unit_state is None
    non_unit_fields = [
        'username', 'display_datetime', 'displayname',
        'mtime', 'type', 'email', 'profile_url']
    proxy_info = proxy.get_submission_info()
    sub_info = quality_check_submission.get_submission_info()
    for k in non_unit_fields:
        assert proxy_info[k] == sub_info[k]
