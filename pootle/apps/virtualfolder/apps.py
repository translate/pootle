# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import importlib

from django.apps import AppConfig


class PootleVirtualFolderConfig(AppConfig):

    name = "virtualfolder"
    verbose_name = "Pootle Virtual Folders"

    def ready(self):
        importlib.import_module("virtualfolder.receivers")
        importlib.import_module("virtualfolder.providers")
        importlib.import_module("virtualfolder.getters")
