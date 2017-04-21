# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import importlib

from django.apps import AppConfig


class PootleChecksConfig(AppConfig):

    name = "pootle_checks"
    verbose_name = "Pootle Checks"

    def ready(self):
        importlib.import_module("pootle_checks.getters")
        importlib.import_module("pootle_checks.receivers")
