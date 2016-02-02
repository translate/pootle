# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pytest_pootle.env import PootleTestEnv


@pytest.fixture(autouse=True, scope='session')
def post_db_setup(_django_db_setup, _django_cursor_wrapper, request):
    with _django_cursor_wrapper:
        PootleTestEnv(request).setup()
