# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import importlib

from django.apps import AppConfig


class PootleFSConfig(AppConfig):

    name = "pootle_fs"
    verbose_name = "Pootle Filesystem synchronisation"
    version = "0.1.4"

    def ready(self):
        importlib.import_module("pootle_fs.models")
        importlib.import_module("pootle_fs.getters")
        importlib.import_module("pootle_fs.providers")
        importlib.import_module("pootle_fs.receivers")
        importlib.import_module("pootle_fs.management.commands.fs")
