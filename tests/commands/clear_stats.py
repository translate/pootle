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
def test_clear_stats(caplog):
    call_command('clear_stats', '--project=project0', '--language=language0',
                 '--verbosity=2')
    infologs = [l.message for l in caplog.records() if l.levelname == "INFO"]
    assert "clear_stats over /language0/project0/" in "".join(infologs)
