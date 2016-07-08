# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from datetime import timedelta

from collections import OrderedDict

import pytest

from pytest_pootle.factories import UserFactory

from django.contrib.auth import get_user_model
from django.db.models import Q

from pootle.core.delegate import contributors
from pootle_statistics.models import Submission
from pootle_statistics.utils import Contributors


User = get_user_model()


def _contributors_list(contribs):
    subs = []
    for user in contribs.user_qs:
        q = Q(submitter=user)
        if contribs.project_codes:
            q = q & Q(
                translation_project__project__code__in=contribs.project_codes)
        if contribs.language_codes:
            q = q & Q(
                translation_project__language__code__in=contribs.language_codes)
        # group the creation_time query
        if contribs.since or contribs.until:
            _q = Q()
            if contribs.since:
                _q = _q & Q(creation_time__gte=contribs.since)
            if contribs.until:
                _q = _q & Q(creation_time__lte=contribs.until)
            q = q & _q
        submissions = Submission.objects.filter(q)
        if submissions.count():
            subs.append(
                (user.username,
                 dict(contributions=submissions.count(),
                      username=user.username,
                      full_name=user.full_name,
                      email=user.email)))
    if contribs.sort_by != "contributions":
        return OrderedDict(
            sorted(
                subs,
                key=lambda i: i[0]))
    return OrderedDict(
        sorted(
            subs,
            key=lambda i: (-i[1]["contributions"], i[1]["username"])))


@pytest.mark.django_db
def test_contributors_delegate():
    contribs_class = contributors.get()
    assert contribs_class is Contributors


@pytest.mark.django_db
def test_contributors_instance(member, anon_submission_unit):
    """Contributors across the site."""
    anon = User.objects.get(username="nobody")
    contribs = Contributors()
    someuser = UserFactory()
    assert contribs.include_anon is False
    assert contribs.language_codes is None
    assert contribs.project_codes is None

    # user_qs
    assert list(contribs.user_qs) == list(User.objects.hide_meta())
    assert someuser in contribs.user_qs
    assert anon not in contribs.user_qs
    assert sorted(contribs.items()) == sorted(contribs.contributors.items())
    assert (
        sorted(contribs)
        == sorted(contribs.contributors)
        == sorted(
            set(contribs.user_qs.filter(contribs.user_filters)
                                .values_list("username", flat=True)))
        == sorted(
            set(contribs.user_qs.filter(submission__gt=0)
                                .values_list("username", flat=True))))

    # contrib object
    for username in contribs:
        assert contribs[username] == contribs.contributors[username]
        assert username in contribs
    assert anon.username not in contribs
    assert someuser.username not in contribs
    assert member.username in contribs
    assert contribs.contributors == _contributors_list(contribs)


@pytest.mark.django_db
def test_contributors_include_anon(member, anon_submission_unit):
    """Contributors across the site."""
    anon = User.objects.get(username="nobody")
    contribs = Contributors(include_anon=True)
    someuser = UserFactory()
    assert contribs.include_anon is True

    # user_qs
    assert (
        list(contribs.user_qs)
        == list(User.objects.exclude(username__in=["system", "default"])))
    assert someuser in contribs.user_qs
    assert anon in contribs.user_qs
    assert (
        sorted(contribs)
        == sorted(contribs.contributors)
        == sorted(
            set(contribs.user_qs.filter(contribs.user_filters)
                                .values_list("username", flat=True)))
        == sorted(
            set(contribs.user_qs.filter(submission__gt=0)
                                .values_list("username", flat=True))))

    # contrib object
    for username in contribs:
        assert contribs[username] == contribs.contributors[username]
        assert username in contribs
    assert anon.username in contribs
    assert contribs.contributors == _contributors_list(contribs)


@pytest.mark.django_db
def test_contributors_filter_projects(member):
    contribs = Contributors(project_codes=["project0"])
    assert contribs.project_codes == ["project0"]
    assert contribs.contributors == _contributors_list(contribs)


@pytest.mark.django_db
def test_contributors_filter_language(member):
    contribs = Contributors(language_codes=["language0"])
    assert contribs.language_codes == ["language0"]
    assert contribs.contributors == _contributors_list(contribs)


@pytest.mark.django_db
def test_contributors_filter_projects_and_language(member):
    contribs = Contributors(
        project_codes=["project0"],
        language_codes=["language0"])
    assert contribs.language_codes == ["language0"]
    assert contribs.project_codes == ["project0"]
    assert contribs.contributors == _contributors_list(contribs)


@pytest.mark.django_db
def test_contributors_filter_projects_since(member):
    sub_times = sorted(set(
        Submission.objects.filter(
            translation_project__project__code="project0").values_list(
                "creation_time", flat=True)))
    start_time = sub_times[0]
    mid_time = sub_times[len(sub_times) / 2]
    end_time = sub_times[-1]

    # get all of of the submissions
    contribs = Contributors(
        project_codes=["project0"],
        since=start_time, until=end_time)
    assert contribs.since == start_time
    assert contribs.until == end_time
    assert contribs.contributors == _contributors_list(contribs)

    # get the first half of the submissions
    contribs = Contributors(
        project_codes=["project0"],
        since=start_time, until=mid_time)
    assert contribs.contributors == _contributors_list(contribs)

    # get the second half of the submissions
    contribs = Contributors(
        project_codes=["project0"],
        since=start_time, until=mid_time)
    assert contribs.contributors == _contributors_list(contribs)

    # try and get submissions before there were any
    contribs = Contributors(
        project_codes=["project0"],
        until=start_time - timedelta(seconds=1))
    assert contribs.contributors == OrderedDict()


@pytest.mark.django_db
def test_contributors_sort_contributions(member, anon_submission_unit):
    """Contributors across the site."""
    contribs = Contributors()
    assert contribs.sort_by == "username"
    contribs = Contributors(sort_by="contributions")
    assert contribs.sort_by == "contributions"
    assert contribs.contributors == _contributors_list(contribs)
