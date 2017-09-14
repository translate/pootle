# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

"""
Pootle App Config
See https://docs.djangoproject.com/en/1.10/ref/applications/
"""

import importlib

from django.apps import AppConfig
from django.core import checks

# imported to force checks to run.  FIXME use AppConfig
from pootle import checks as pootle_checks  # noqa
from pootle.core.utils import deprecation


class PootleConfig(AppConfig):
    name = "pootle_app"
    verbose_name = "Pootle"
    version = "0.0.8"

    def ready(self):
        checks.register(deprecation.check_deprecated_settings, "settings")
        importlib.import_module("pootle_app.getters")
        importlib.import_module("pootle_app.providers")
