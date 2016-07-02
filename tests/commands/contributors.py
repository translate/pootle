# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from argparse import ArgumentTypeError
from dateutil.parser import parse as parse_datetime

import pytest

from django.core.management import call_command

from pootle.core.utils.timezone import make_aware
from pootle_app.management.commands.contributors import get_aware_datetime
from pootle_store.models import Unit


def test_contributors_get_aware_datetime():
    """Get an aware datetime from a valid string."""
    iso_datetime = make_aware(parse_datetime("2016-01-24T23:15:22+0000"))

    # Test ISO 8601 datetime.
    assert iso_datetime == get_aware_datetime("2016-01-24T23:15:22+0000")

    # Test git-like datetime.
    assert iso_datetime == get_aware_datetime("2016-01-24 23:15:22 +0000")

    # Test just an ISO 8601 date.
    iso_datetime = make_aware(parse_datetime("2016-01-24T00:00:00+0000"))
    assert iso_datetime == get_aware_datetime("2016-01-24")

    # Test None.
    assert get_aware_datetime(None) is None

    # Test empty string.
    assert get_aware_datetime("") is None

    # Test non-empty string.
    with pytest.raises(ArgumentTypeError):
        get_aware_datetime("THIS FAILS")

    # Test blank string.
    with pytest.raises(ArgumentTypeError):
        get_aware_datetime(" ")


@pytest.mark.cmd
@pytest.mark.django_db
def test_contributors_noargs(capfd, en_tutorial_po_member_updated):
    """Contributors across the site."""
    call_command('contributors')
    out, err = capfd.readouterr()
    contribs = Unit.objects.filter(submitted_by__username="member")
    assert ("Member (%d contributions)" % contribs.count()) in out


@pytest.mark.cmd
@pytest.mark.django_db
def test_contributors_project(capfd, en_tutorial_po_member_updated):
    """Contributors in a given project."""
    call_command('contributors', '--project=tutorial')
    out, err = capfd.readouterr()
    contribs = Unit.objects.filter(
        submitted_by__username="member",
        store__translation_project__project__code="tutorial")
    assert ("Member (%d contributions)" % contribs.count()) in out


@pytest.mark.cmd
@pytest.mark.django_db
def test_contributors_language(capfd, en_tutorial_po_member_updated):
    """Contributors in a given language."""
    call_command('contributors', '--language=en')
    out, err = capfd.readouterr()
    contribs = Unit.objects.filter(
        submitted_by__username="member",
        store__translation_project__language__code="en")
    assert ("Member (%d contributions)" % contribs.count()) in out


@pytest.mark.cmd
@pytest.mark.django_db
def test_contributors_sort(capfd, en_tutorial_po_member_updated, member):
    """Contributors in contribution order."""
    member.email = "member@test.email"
    member.save()
    contribs = Unit.objects.filter(submitted_by__username="member")
    call_command('contributors', '--sort-by=contributions')
    out, err = capfd.readouterr()
    assert (
        ("Member <member@test.email> (%d contributions)" % contribs.count())
        in out)
