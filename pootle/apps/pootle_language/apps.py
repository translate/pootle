# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle language. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import importlib

from django.apps import AppConfig


class PootleLanguageConfig(AppConfig):

    name = "pootle_language"
    verbose_name = "Pootle Language"
    version = "0.1.5"

    def ready(self):
        importlib.import_module("pootle_language.getters")
        importlib.import_module("pootle_language.receivers")
