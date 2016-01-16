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
def test_revision(capfd):
    """Get current revision."""
    call_command('revision')
    out, err = capfd.readouterr()
    assert out.rstrip().isnumeric()


@pytest.mark.cmd
@pytest.mark.django_db
def test_revision_restore(capfd):
    """Restore redis revision from DB."""
    call_command('revision', '--restore')
    out, err = capfd.readouterr()
    assert out.rstrip().isnumeric()
