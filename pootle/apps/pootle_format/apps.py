# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import importlib

from django.apps import AppConfig


class PootleFormatConfig(AppConfig):

    name = "pootle_format"
    verbose_name = "Pootle Format"

    def ready(self):
        importlib.import_module("pootle_format.models")
        importlib.import_module("pootle_format.receivers")
        importlib.import_module("pootle_format.getters")
        importlib.import_module("pootle_format.providers")
        importlib.import_module("pootle_format.formats.providers")
