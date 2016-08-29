# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import importlib

from django.apps import AppConfig


class PootleStoreConfig(AppConfig):

    name = "pootle_store"
    verbose_name = "Pootle Store"

    def ready(self):
        importlib.import_module("pootle_store.getters")
        importlib.import_module("pootle_store.providers")
        importlib.import_module("pootle_store.receivers")
