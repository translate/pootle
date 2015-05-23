#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

"""
Pootle App Config
See https://docs.djangoproject.com/en/1.7/ref/applications/
"""

from django.apps import AppConfig
from django.core import checks

from pootle import checks as pootle_checks
from pootle.core.utils import deprecation


class PootleConfig(AppConfig):
    name = "pootle_app"
    verbose_name = "Pootle"

    def ready(self):
        # FIXME In Django 1.8 this needs to change to
        # register(settings.check_deprecated_settings, "settings")
        checks.register("settings")(deprecation.check_deprecated_settings)
