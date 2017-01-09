# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os

from django import setup
from django.conf import settings

import logging

logging.getLogger("factory").setLevel(logging.WARN)


def pytest_configure():
    if not settings.configured:
        from pootle import syspath_override  # Needed for monkey-patching
        syspath_override
        os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'
        WORKING_DIR = os.path.abspath(os.path.dirname(__file__))
        os.environ['POOTLE_SETTINGS'] = os.path.join(WORKING_DIR,
                                                     'settings.py')
        # The call to `setup()` was needed before a fix for
        # pytest-dev/pytest-django#146 was available. This happened in version
        # 2.9; unfortunately upgrading to 2.9+ is not possible yet because a fix
        # for pytest-dev/pytest-django#289 is needed too, and this is not part
        # of any releases for the time being.
        setup()
