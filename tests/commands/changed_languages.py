# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.core.management import call_command


@pytest.mark.cmd
@pytest.mark.django_db
def test_changed_languages_noargs(capfd, afrikaans_tutorial, french_tutorial,
                                  revision):
    """Get changed languages since last sync."""
    call_command('changed_languages')
    out, err = capfd.readouterr()
    assert "(no known changes)" in err
    assert ("Will show languages changed between revisions 6 (exclusive) and "
            "6 (inclusive)" in err)


@pytest.mark.cmd
@pytest.mark.django_db
def test_changed_languages_since_revision(capfd, afrikaans_tutorial,
                                          french_tutorial, revision):
    """Changed languages since a given revision"""
    # Everything
    call_command('changed_languages', '--after-revision=0')
    out, err = capfd.readouterr()
    assert "af,fr" in out
    # End revisions
    call_command('changed_languages', '--after-revision=4')
    out, err = capfd.readouterr()
    assert "fr" in out
