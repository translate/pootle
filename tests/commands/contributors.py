# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.core.management import call_command

from pootle_store.models import Unit


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
def test_contributors_revision(capfd, en_tutorial_po_member_updated):
    """Contributors since a given revision."""
    call_command('contributors', '--from-revision=1')
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
