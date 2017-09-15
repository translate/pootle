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


class PootleTPConfig(AppConfig):
    name = "pootle_translationproject"
    verbose_name = "PootleTranslationProject"
    version = "0.1.5"

    def ready(self):
        importlib.import_module("pootle_translationproject.receivers")
        importlib.import_module("pootle_translationproject.getters")
