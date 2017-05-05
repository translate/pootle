# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from collections import OrderedDict

import pytest


CONTRIBUTORS_KWARGS = dict(
    noargs={},
    projects=dict(project_codes=[u"project0"]),
    languages=dict(language_codes=[u"language0"]),
    projects_and_languages=dict(
        project_codes=[u"project0"],
        language_codes=[u"language0"]),
    since=dict(since="2000-11-10"),
    until=dict(until="2000-11-10"),
    since_and_until=dict(since="2000-11-10", until="2000-11-10"),
    sort_by=dict(sort_by="contributions"))


CONTRIBUTORS_WITH_EMAIL = OrderedDict((
    ('admin', {
        'username': 'admin',
        'full_name': '',
        'email': '',
    }),
    ('member', {
        'username': 'member',
        'full_name': '',
        'email': 'member@membership.us',
    }),
    ('funkymember', {
        'username': 'funkymember',
        'full_name': 'Funky " member with <> and @ and stuff',
        'email': 'funky_member@membership.dk',
    }),
    ('fullmember', {
        'username': 'fullmember',
        'full_name': 'Just a member',
        'email': 'full_member@membership.fr',
    }),
    ('comma_member', {
        'username': 'comma_member',
        'full_name': 'Member, with comma',
        'email': 'comma_member@membership.de',
    }),
))


@pytest.fixture
def default_contributors_kwargs():
    return OrderedDict(
        (("include_anon", False),
         ("since", None),
         ("until", None),
         ("project_codes", None),
         ("language_codes", None),
         ("sort_by", "username"),
         ("mailmerge", False)))


@pytest.fixture(params=CONTRIBUTORS_KWARGS)
def contributors_kwargs(request):
    return CONTRIBUTORS_KWARGS[request.param]


@pytest.fixture
def dummy_contributors(request, default_contributors_kwargs):
    from pootle.core.delegate import contributors
    from pootle.core.plugin import getter

    from pootle_statistics.utils import Contributors

    orig_receivers = contributors.receivers
    receivers_cache = contributors.sender_receivers_cache.copy()
    contributors.receivers = []
    contributors.sender_receivers_cache.clear()

    class DummyContributors(Contributors):

        @property
        def contributors(self):
            # Hack the output to get back our kwargs.
            _result_kwargs = OrderedDict()
            for k in default_contributors_kwargs.keys():
                _result_kwargs[k] = dict(
                    full_name=k,
                    contributions=getattr(
                        self, k, default_contributors_kwargs[k]))
            return _result_kwargs

    @getter(contributors, weak=False)
    def get_dummy_contribs_(**kwargs_):
        return DummyContributors

    def _reset_contributors():
        contributors.receivers = orig_receivers
        contributors.sender_receivers_cache = receivers_cache

    request.addfinalizer(_reset_contributors)


@pytest.fixture
def dummy_email_contributors(request):
    from pootle.core.delegate import contributors
    from pootle.core.plugin import getter

    from pootle_statistics.utils import Contributors

    orig_receivers = contributors.receivers
    receivers_cache = contributors.sender_receivers_cache.copy()
    contributors.receivers = []
    contributors.sender_receivers_cache.clear()

    class DummyContributors(Contributors):

        @property
        def contributors(self):
            return OrderedDict(
                sorted(CONTRIBUTORS_WITH_EMAIL.items(),
                       key=lambda x: str.lower(x[1]['username'])))

    @getter(contributors, weak=False)
    def get_dummy_contribs_(**kwargs_):
        return DummyContributors

    def _reset_contributors():
        contributors.receivers = orig_receivers
        contributors.sender_receivers_cache = receivers_cache

    request.addfinalizer(_reset_contributors)
