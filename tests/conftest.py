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
        setup()  # Required until pytest-dev/pytest-django#146 is fixed


pytest_plugins = 'pytest_pootle.plugin'
