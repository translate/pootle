# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.core.management import call_command
from django.core.management.base import CommandError


@pytest.mark.cmd
@pytest.mark.django_db
def test_flush_cache(capfd):
    call_command('flush_cache', '--rqdata')
    out, err = capfd.readouterr()
    assert "Flushing cache..." in out
    assert "RQ data removed." in out
    assert "Max unit revision restored." in out


@pytest.mark.cmd
@pytest.mark.django_db
def test_flush_cache_no_options():
    with pytest.raises(CommandError) as e:
        call_command('flush_cache')
    assert "No options were provided." in str(e)
